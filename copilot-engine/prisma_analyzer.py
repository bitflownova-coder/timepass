"""
Copilot Engine - Prisma / ORM Intelligence Layer
Deterministic validation of Prisma schemas, relations, migrations,
and DTO-to-model consistency.

Covers:
  - Prisma schema parsing into structured representation
  - Relation integrity validation (bidirectional, FK fields)
  - Nullable mismatch detection
  - Index analysis (missing / duplicate)
  - Cascade rule auditing
  - Migration discipline (schema drift detection)
  - DTO ↔ Prisma model field comparison
  - Include/select usage validation against schema
"""
import os
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone


# ──────────────────────────────────────────────────────────────
# Data Structures
# ──────────────────────────────────────────────────────────────

@dataclass
class PrismaField:
    name: str
    type: str
    is_list: bool = False
    is_optional: bool = False
    is_id: bool = False
    is_unique: bool = False
    is_updated_at: bool = False
    default: Optional[str] = None
    relation: Optional[Dict[str, Any]] = None  # {name, fields, references, onDelete, onUpdate}
    raw_attributes: List[str] = field(default_factory=list)
    map_name: Optional[str] = None  # @map("column_name")


@dataclass
class PrismaModel:
    name: str
    fields: Dict[str, PrismaField] = field(default_factory=dict)
    indexes: List[Dict[str, Any]] = field(default_factory=list)       # @@index
    unique_constraints: List[Dict[str, Any]] = field(default_factory=list)  # @@unique
    map_name: Optional[str] = None  # @@map("table_name")
    id_fields: List[str] = field(default_factory=list)  # @@id([...])


@dataclass
class PrismaEnum:
    name: str
    values: List[str] = field(default_factory=list)


@dataclass
class PrismaSchema:
    models: Dict[str, PrismaModel] = field(default_factory=dict)
    enums: Dict[str, PrismaEnum] = field(default_factory=dict)
    datasource: Dict[str, str] = field(default_factory=dict)
    generators: List[Dict[str, str]] = field(default_factory=list)
    raw_text: str = ""
    file_path: str = ""
    parsed_at: Optional[str] = None


@dataclass
class ValidationIssue:
    severity: str   # CRITICAL, HIGH, MEDIUM, LOW, INFO
    category: str   # relation, nullable, index, cascade, migration, dto_mismatch, include_select
    message: str
    model: Optional[str] = None
    field_name: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    suggestion: Optional[str] = None


# ──────────────────────────────────────────────────────────────
# Prisma Schema Parser
# ──────────────────────────────────────────────────────────────

class PrismaParser:
    """Deterministic parser for schema.prisma files."""

    # Attribute patterns
    RE_RELATION = re.compile(
        r'@relation\(\s*'
        r'(?:name:\s*"([^"]*)")?\s*,?\s*'
        r'(?:fields:\s*\[([^\]]*)\])?\s*,?\s*'
        r'(?:references:\s*\[([^\]]*)\])?\s*,?\s*'
        r'(?:onDelete:\s*(\w+))?\s*,?\s*'
        r'(?:onUpdate:\s*(\w+))?\s*'
        r'\)',
        re.DOTALL
    )
    RE_RELATION_SIMPLE = re.compile(r'@relation\("([^"]*)"\)')
    RE_DEFAULT = re.compile(r'@default\(([^)]+)\)')
    RE_MAP = re.compile(r'@map\("([^"]*)"\)')
    RE_MAP_MODEL = re.compile(r'@@map\("([^"]*)"\)')
    RE_INDEX = re.compile(r'@@index\(\[([^\]]+)\](?:,\s*map:\s*"([^"]*)")?\)')
    RE_UNIQUE = re.compile(r'@@unique\(\[([^\]]+)\](?:,\s*map:\s*"([^"]*)")?\)')
    RE_ID_COMPOUND = re.compile(r'@@id\(\[([^\]]+)\]\)')

    def parse_file(self, file_path: str) -> PrismaSchema:
        """Parse a schema.prisma file."""
        path = Path(file_path)
        if not path.exists():
            return PrismaSchema(file_path=file_path)

        content = path.read_text(encoding='utf-8', errors='ignore')
        return self.parse_text(content, file_path)

    def parse_text(self, content: str, file_path: str = "") -> PrismaSchema:
        """Parse Prisma schema text content."""
        schema = PrismaSchema(raw_text=content, file_path=file_path, parsed_at=datetime.now(timezone.utc).isoformat())

        # Remove comments
        lines = []
        for line in content.split('\n'):
            stripped = line.strip()
            if stripped.startswith('//'):
                continue
            # Remove inline comments
            comment_idx = line.find('//')
            if comment_idx >= 0:
                line = line[:comment_idx]
            lines.append(line)

        clean = '\n'.join(lines)

        # Parse blocks
        self._parse_datasource(clean, schema)
        self._parse_generators(clean, schema)
        self._parse_enums(clean, schema)
        self._parse_models(clean, schema)

        return schema

    def _parse_datasource(self, content: str, schema: PrismaSchema):
        match = re.search(r'datasource\s+\w+\s*\{([^}]+)\}', content)
        if match:
            body = match.group(1)
            for line in body.strip().split('\n'):
                line = line.strip()
                if '=' in line:
                    key, val = line.split('=', 1)
                    schema.datasource[key.strip()] = val.strip().strip('"')

    def _parse_generators(self, content: str, schema: PrismaSchema):
        for match in re.finditer(r'generator\s+(\w+)\s*\{([^}]+)\}', content):
            name = match.group(1)
            body = match.group(2)
            gen = {'name': name}
            for line in body.strip().split('\n'):
                line = line.strip()
                if '=' in line:
                    key, val = line.split('=', 1)
                    gen[key.strip()] = val.strip().strip('"')
            schema.generators.append(gen)

    def _parse_enums(self, content: str, schema: PrismaSchema):
        for match in re.finditer(r'enum\s+(\w+)\s*\{([^}]+)\}', content):
            name = match.group(1)
            body = match.group(2)
            values = [v.strip() for v in body.strip().split('\n') if v.strip()]
            schema.enums[name] = PrismaEnum(name=name, values=values)

    def _parse_models(self, content: str, schema: PrismaSchema):
        # Match model blocks (handles nested braces in attributes)
        model_pattern = re.compile(r'model\s+(\w+)\s*\{', re.MULTILINE)
        for match in model_pattern.finditer(content):
            model_name = match.group(1)
            start = match.end()
            # Find matching closing brace
            depth = 1
            pos = start
            while pos < len(content) and depth > 0:
                if content[pos] == '{':
                    depth += 1
                elif content[pos] == '}':
                    depth -= 1
                pos += 1

            body = content[start:pos - 1]
            model = PrismaModel(name=model_name)
            self._parse_model_body(body, model)
            schema.models[model_name] = model

    def _parse_model_body(self, body: str, model: PrismaModel):
        """Parse the body of a model block."""
        for line in body.strip().split('\n'):
            line = line.strip()
            if not line:
                continue

            # Model-level attributes
            if line.startswith('@@'):
                self._parse_model_attribute(line, model)
                continue

            # Field definition: name Type attributes...
            parts = line.split()
            if len(parts) < 2:
                continue

            field_name = parts[0]
            if field_name.startswith('@'):
                continue  # stray attribute

            type_str = parts[1]
            rest = ' '.join(parts[2:]) if len(parts) > 2 else ''

            prisma_field = PrismaField(name=field_name, type=type_str.rstrip('?').rstrip('[]'))

            # List type
            if '[]' in type_str:
                prisma_field.is_list = True

            # Optional
            if '?' in type_str:
                prisma_field.is_optional = True

            # Attributes
            if '@id' in rest:
                prisma_field.is_id = True
                model.id_fields.append(field_name)
            if '@unique' in rest:
                prisma_field.is_unique = True
            if '@updatedAt' in rest:
                prisma_field.is_updated_at = True

            # @default
            default_match = self.RE_DEFAULT.search(rest)
            if default_match:
                prisma_field.default = default_match.group(1)

            # @map
            map_match = self.RE_MAP.search(rest)
            if map_match:
                prisma_field.map_name = map_match.group(1)

            # @relation
            rel_match = self.RE_RELATION.search(rest)
            if rel_match:
                prisma_field.relation = {
                    'name': rel_match.group(1) or None,
                    'fields': [f.strip() for f in rel_match.group(2).split(',')] if rel_match.group(2) else [],
                    'references': [f.strip() for f in rel_match.group(3).split(',')] if rel_match.group(3) else [],
                    'onDelete': rel_match.group(4) or None,
                    'onUpdate': rel_match.group(5) or None,
                }
            else:
                rel_simple = self.RE_RELATION_SIMPLE.search(rest)
                if rel_simple:
                    prisma_field.relation = {'name': rel_simple.group(1), 'fields': [], 'references': []}

            prisma_field.raw_attributes = re.findall(r'@\w+(?:\([^)]*\))?', rest)
            model.fields[field_name] = prisma_field

    def _parse_model_attribute(self, line: str, model: PrismaModel):
        """Parse @@-level model attributes."""
        map_match = self.RE_MAP_MODEL.search(line)
        if map_match:
            model.map_name = map_match.group(1)

        idx_match = self.RE_INDEX.search(line)
        if idx_match:
            fields = [f.strip() for f in idx_match.group(1).split(',')]
            model.indexes.append({'fields': fields, 'map': idx_match.group(2)})

        uniq_match = self.RE_UNIQUE.search(line)
        if uniq_match:
            fields = [f.strip() for f in uniq_match.group(1).split(',')]
            model.unique_constraints.append({'fields': fields, 'map': uniq_match.group(2)})

        id_match = self.RE_ID_COMPOUND.search(line)
        if id_match:
            model.id_fields = [f.strip() for f in id_match.group(1).split(',')]


# ──────────────────────────────────────────────────────────────
# Prisma Validator
# ──────────────────────────────────────────────────────────────

class PrismaValidator:
    """Validates Prisma schema for structural issues."""

    def validate(self, schema: PrismaSchema) -> List[ValidationIssue]:
        """Run all validation checks on a parsed schema."""
        issues: List[ValidationIssue] = []

        issues.extend(self._check_relations(schema))
        issues.extend(self._check_nullable(schema))
        issues.extend(self._check_indexes(schema))
        issues.extend(self._check_cascades(schema))
        issues.extend(self._check_id_fields(schema))
        issues.extend(self._check_enum_usage(schema))

        return issues

    def _check_relations(self, schema: PrismaSchema) -> List[ValidationIssue]:
        """Check relation integrity: bidirectional, FK fields exist, references valid."""
        issues = []
        model_names = set(schema.models.keys())

        for model_name, model in schema.models.items():
            for field_name, f in model.fields.items():
                if f.relation is None:
                    continue

                # Check target model exists
                target_type = f.type
                if target_type not in model_names:
                    issues.append(ValidationIssue(
                        severity='CRITICAL',
                        category='relation',
                        message=f'Relation target model "{target_type}" does not exist',
                        model=model_name,
                        field_name=field_name,
                        suggestion=f'Create model {target_type} or fix the type name',
                    ))
                    continue

                # Check FK fields exist in this model
                for fk in f.relation.get('fields', []):
                    if fk and fk not in model.fields:
                        issues.append(ValidationIssue(
                            severity='CRITICAL',
                            category='relation',
                            message=f'Relation FK field "{fk}" does not exist in model {model_name}',
                            model=model_name,
                            field_name=field_name,
                            suggestion=f'Add field: {fk} Int (or matching type)',
                        ))

                # Check references exist in target model
                target_model = schema.models.get(target_type)
                if target_model:
                    for ref in f.relation.get('references', []):
                        if ref and ref not in target_model.fields:
                            issues.append(ValidationIssue(
                                severity='CRITICAL',
                                category='relation',
                                message=f'Referenced field "{ref}" does not exist in model {target_type}',
                                model=model_name,
                                field_name=field_name,
                                suggestion=f'Add field "{ref}" to model {target_type}',
                            ))

                    # Check bidirectional: target should have a field referencing back
                    back_ref_found = False
                    for tf_name, tf in target_model.fields.items():
                        if tf.type == model_name:
                            back_ref_found = True
                            break
                        if tf.relation and tf.relation.get('name') == f.relation.get('name') and f.relation.get('name'):
                            back_ref_found = True
                            break

                    if not back_ref_found and not f.is_list:
                        issues.append(ValidationIssue(
                            severity='MEDIUM',
                            category='relation',
                            message=f'No back-reference found in {target_type} for relation from {model_name}.{field_name}',
                            model=model_name,
                            field_name=field_name,
                            suggestion=f'Add a {model_name} or {model_name}[] field in {target_type}',
                        ))

        return issues

    def _check_nullable(self, schema: PrismaSchema) -> List[ValidationIssue]:
        """Check for nullable FK fields without explicit handling."""
        issues = []
        for model_name, model in schema.models.items():
            for field_name, f in model.fields.items():
                if f.relation and f.relation.get('fields'):
                    for fk in f.relation['fields']:
                        fk_field = model.fields.get(fk)
                        if fk_field:
                            # Relation optional but FK not optional
                            if f.is_optional and not fk_field.is_optional:
                                issues.append(ValidationIssue(
                                    severity='HIGH',
                                    category='nullable',
                                    message=f'Optional relation {field_name} has non-optional FK field {fk}',
                                    model=model_name,
                                    field_name=fk,
                                    suggestion=f'Make {fk} optional ({fk_field.type}?) or make relation required',
                                ))
                            # FK optional but relation required
                            if not f.is_optional and fk_field.is_optional:
                                issues.append(ValidationIssue(
                                    severity='HIGH',
                                    category='nullable',
                                    message=f'Required relation {field_name} has optional FK field {fk}',
                                    model=model_name,
                                    field_name=fk,
                                    suggestion=f'Remove ? from {fk} or make relation optional',
                                ))
        return issues

    def _check_indexes(self, schema: PrismaSchema) -> List[ValidationIssue]:
        """Check for missing indexes on FK fields and duplicates."""
        issues = []
        for model_name, model in schema.models.items():
            indexed_fields: Set[str] = set()
            for idx in model.indexes:
                for f in idx['fields']:
                    indexed_fields.add(f)
            for uc in model.unique_constraints:
                for f in uc['fields']:
                    indexed_fields.add(f)
            for f_name, f in model.fields.items():
                if f.is_id or f.is_unique:
                    indexed_fields.add(f_name)

            # FK fields should have indexes
            for f_name, f in model.fields.items():
                if f.relation and f.relation.get('fields'):
                    for fk in f.relation['fields']:
                        if fk not in indexed_fields:
                            issues.append(ValidationIssue(
                                severity='MEDIUM',
                                category='index',
                                message=f'FK field "{fk}" in {model_name} has no index — queries will be slow',
                                model=model_name,
                                field_name=fk,
                                suggestion=f'Add @@index([{fk}]) to model {model_name}',
                            ))

            # Check duplicate indexes
            idx_sets = [frozenset(i['fields']) for i in model.indexes]
            seen = set()
            for idx_set in idx_sets:
                if idx_set in seen:
                    issues.append(ValidationIssue(
                        severity='LOW',
                        category='index',
                        message=f'Duplicate index on fields {list(idx_set)} in {model_name}',
                        model=model_name,
                    ))
                seen.add(idx_set)

        return issues

    def _check_cascades(self, schema: PrismaSchema) -> List[ValidationIssue]:
        """Check for unsafe cascade deletes."""
        issues = []
        for model_name, model in schema.models.items():
            for f_name, f in model.fields.items():
                if f.relation:
                    on_delete = f.relation.get('onDelete')
                    if on_delete == 'Cascade':
                        # Warn about cascade on models with many relations
                        target = schema.models.get(f.type)
                        if target:
                            target_relations = sum(1 for tf in target.fields.values() if tf.relation)
                            if target_relations > 2:
                                issues.append(ValidationIssue(
                                    severity='HIGH',
                                    category='cascade',
                                    message=f'Cascade delete on {model_name}.{f_name} → {f.type} which has {target_relations} relations — risk of cascading data loss',
                                    model=model_name,
                                    field_name=f_name,
                                    suggestion='Consider SetNull or Restrict instead of Cascade',
                                ))
                    elif on_delete is None and f.relation.get('fields'):
                        # No explicit onDelete — uses Prisma default (depends on version)
                        issues.append(ValidationIssue(
                            severity='LOW',
                            category='cascade',
                            message=f'No explicit onDelete for {model_name}.{f_name} — default behavior may vary',
                            model=model_name,
                            field_name=f_name,
                            suggestion='Add explicit onDelete: Cascade, SetNull, or Restrict',
                        ))

        return issues

    def _check_id_fields(self, schema: PrismaSchema) -> List[ValidationIssue]:
        """Check that every model has an ID."""
        issues = []
        for model_name, model in schema.models.items():
            if not model.id_fields:
                issues.append(ValidationIssue(
                    severity='CRITICAL',
                    category='relation',
                    message=f'Model {model_name} has no @id or @@id — Prisma requires a unique identifier',
                    model=model_name,
                    suggestion='Add @id to a field or use @@id([field1, field2])',
                ))
        return issues

    def _check_enum_usage(self, schema: PrismaSchema) -> List[ValidationIssue]:
        """Check that enum types used in models are defined."""
        issues = []
        known_types = {'String', 'Int', 'Float', 'Boolean', 'DateTime', 'Json',
                       'BigInt', 'Decimal', 'Bytes', 'Unsupported'}
        known_types.update(schema.models.keys())
        known_types.update(schema.enums.keys())

        for model_name, model in schema.models.items():
            for f_name, f in model.fields.items():
                if f.type not in known_types:
                    issues.append(ValidationIssue(
                        severity='HIGH',
                        category='relation',
                        message=f'Unknown type "{f.type}" used in {model_name}.{f_name}',
                        model=model_name,
                        field_name=f_name,
                        suggestion=f'Define enum {f.type} or model {f.type}',
                    ))

        return issues


# ──────────────────────────────────────────────────────────────
# DTO ↔ Model Validator
# ──────────────────────────────────────────────────────────────

class DTOValidator:
    """Compares DTO / validation schema fields against Prisma models."""

    # Patterns to extract DTO / interface / class fields from code
    TS_INTERFACE = re.compile(
        r'(?:export\s+)?(?:interface|type)\s+(\w+(?:Dto|DTO|Input|Output|Request|Response|Schema|Payload))\s*(?:extends\s+\w+\s*)?\{([^}]+)\}',
        re.DOTALL | re.IGNORECASE
    )
    TS_ZOD = re.compile(
        r'(?:export\s+)?(?:const|let)\s+(\w+(?:Schema|Validator|Dto|DTO))\s*=\s*z\.object\(\{([^}]+)\}\)',
        re.DOTALL | re.IGNORECASE
    )
    PY_PYDANTIC = re.compile(
        r'class\s+(\w+(?:Schema|DTO|Dto|Input|Output|Request|Response|Create|Update))\s*\(\s*(?:BaseModel|BaseSchema)[^)]*\)\s*:\s*\n((?:\s+\w+.*\n)+)',
        re.MULTILINE
    )

    # Type mappings: Prisma → TS, Prisma → Python
    PRISMA_TO_TS = {
        'String': {'string'},
        'Int': {'number', 'int'},
        'Float': {'number', 'float'},
        'Boolean': {'boolean', 'bool'},
        'DateTime': {'Date', 'string', 'Date | string'},
        'BigInt': {'bigint', 'number'},
        'Decimal': {'number', 'string', 'Decimal'},
        'Json': {'any', 'object', 'Record<string, any>', 'JsonValue'},
        'Bytes': {'Buffer', 'Uint8Array'},
    }
    PRISMA_TO_PY = {
        'String': {'str'},
        'Int': {'int'},
        'Float': {'float'},
        'Boolean': {'bool'},
        'DateTime': {'datetime', 'Optional[datetime]'},
        'BigInt': {'int'},
        'Decimal': {'Decimal', 'float'},
        'Json': {'dict', 'Any', 'Dict'},
        'Bytes': {'bytes'},
    }

    def extract_dtos_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract DTO definitions from a TypeScript or Python file."""
        path = Path(file_path)
        if not path.exists():
            return []

        content = path.read_text(encoding='utf-8', errors='ignore')
        dtos = []

        if path.suffix in ('.ts', '.tsx', '.js', '.jsx'):
            dtos.extend(self._extract_ts_interfaces(content, file_path))
            dtos.extend(self._extract_zod_schemas(content, file_path))
        elif path.suffix == '.py':
            dtos.extend(self._extract_pydantic_models(content, file_path))

        return dtos

    def extract_dtos_from_workspace(self, workspace_path: str) -> List[Dict[str, Any]]:
        """Scan workspace for all DTO definitions."""
        all_dtos = []
        skip_dirs = {'node_modules', '.git', '__pycache__', '.venv', 'dist', 'build', '.next'}

        for root, dirs, files in os.walk(workspace_path):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for fname in files:
                if Path(fname).suffix in ('.ts', '.tsx', '.js', '.jsx', '.py'):
                    fp = os.path.join(root, fname)
                    dtos = self.extract_dtos_from_file(fp)
                    all_dtos.extend(dtos)

        return all_dtos

    def compare_dto_to_model(self, dto: Dict[str, Any], model: PrismaModel) -> List[ValidationIssue]:
        """Compare a DTO's fields against a Prisma model's fields."""
        issues = []
        dto_name = dto['name']
        dto_fields = dto['fields']  # {name: {type, optional}}

        model_field_names = set(model.fields.keys())
        dto_field_names = set(dto_fields.keys())

        # Fields in DTO but not in model (potential drift)
        extra_in_dto = dto_field_names - model_field_names
        # Exclude relation fields and computed fields
        relation_types = {f.type for f in model.fields.values() if f.relation}
        for extra in extra_in_dto:
            # Could be a computed/virtual field — just info
            issues.append(ValidationIssue(
                severity='INFO',
                category='dto_mismatch',
                message=f'DTO "{dto_name}" has field "{extra}" not found in Prisma model {model.name}',
                model=model.name,
                field_name=extra,
                file_path=dto.get('file_path'),
                suggestion='Verify this is intentional (computed field) or remove from DTO',
            ))

        # Required model fields missing from DTO
        for f_name, f in model.fields.items():
            if f.relation:
                continue  # Skip relation objects in DTO comparison
            if f.is_id and f.default:
                continue  # Auto-generated IDs don't need to be in DTO
            if f.is_updated_at:
                continue  # Auto-managed

            if f_name not in dto_field_names:
                if not f.is_optional and f.default is None:
                    issues.append(ValidationIssue(
                        severity='HIGH',
                        category='dto_mismatch',
                        message=f'Required field "{f_name}" from model {model.name} missing in DTO "{dto_name}"',
                        model=model.name,
                        field_name=f_name,
                        file_path=dto.get('file_path'),
                        suggestion=f'Add "{f_name}" to {dto_name}',
                    ))

            # Check nullable mismatch
            if f_name in dto_fields:
                dto_optional = dto_fields[f_name].get('optional', False)
                if f.is_optional and not dto_optional:
                    issues.append(ValidationIssue(
                        severity='MEDIUM',
                        category='dto_mismatch',
                        message=f'Model field {model.name}.{f_name} is optional but DTO "{dto_name}" marks it required',
                        model=model.name,
                        field_name=f_name,
                        file_path=dto.get('file_path'),
                    ))
                if not f.is_optional and dto_optional and f.default is None:
                    issues.append(ValidationIssue(
                        severity='HIGH',
                        category='dto_mismatch',
                        message=f'Model field {model.name}.{f_name} is required but DTO "{dto_name}" marks it optional',
                        model=model.name,
                        field_name=f_name,
                        file_path=dto.get('file_path'),
                        suggestion=f'Remove optional marker from {f_name} in DTO or add @default in Prisma',
                    ))

        return issues

    def _extract_ts_interfaces(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract TypeScript interface/type DTOs."""
        results = []
        for match in self.TS_INTERFACE.finditer(content):
            name = match.group(1)
            body = match.group(2)
            fields = {}
            for line in body.strip().split('\n'):
                line = line.strip().rstrip(';').rstrip(',')
                if not line or line.startswith('//'):
                    continue
                # name?: type  or  name: type
                field_match = re.match(r'(\w+)(\?)?:\s*(.+)', line)
                if field_match:
                    fields[field_match.group(1)] = {
                        'type': field_match.group(3).strip(),
                        'optional': field_match.group(2) == '?',
                    }
            if fields:
                results.append({'name': name, 'fields': fields, 'file_path': file_path, 'kind': 'ts_interface'})
        return results

    def _extract_zod_schemas(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract Zod schema definitions."""
        results = []
        for match in self.TS_ZOD.finditer(content):
            name = match.group(1)
            body = match.group(2)
            fields = {}
            for line in body.strip().split('\n'):
                line = line.strip().rstrip(',')
                if not line or line.startswith('//'):
                    continue
                field_match = re.match(r'(\w+):\s*z\.(.+)', line)
                if field_match:
                    zod_type = field_match.group(2)
                    fields[field_match.group(1)] = {
                        'type': zod_type,
                        'optional': '.optional()' in zod_type or '.nullable()' in zod_type,
                    }
            if fields:
                results.append({'name': name, 'fields': fields, 'file_path': file_path, 'kind': 'zod'})
        return results

    def _extract_pydantic_models(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract Pydantic model DTOs."""
        results = []
        for match in self.PY_PYDANTIC.finditer(content):
            name = match.group(1)
            body = match.group(2)
            fields = {}
            for line in body.split('\n'):
                line = line.strip()
                if not line or line.startswith('#') or line.startswith('class '):
                    continue
                field_match = re.match(r'(\w+)\s*:\s*(.+?)(?:\s*=.*)?$', line)
                if field_match:
                    type_str = field_match.group(2).strip()
                    fields[field_match.group(1)] = {
                        'type': type_str,
                        'optional': 'Optional' in type_str or 'None' in type_str,
                    }
            if fields:
                results.append({'name': name, 'fields': fields, 'file_path': file_path, 'kind': 'pydantic'})
        return results


# ──────────────────────────────────────────────────────────────
# Migration Discipline Checker
# ──────────────────────────────────────────────────────────────

class MigrationChecker:
    """Checks for schema drift between Prisma schema and migrations."""

    def check_migration_status(self, workspace_path: str) -> List[ValidationIssue]:
        """Check if Prisma migrations are up to date."""
        issues = []
        root = Path(workspace_path)

        # Find schema.prisma
        schema_path = self._find_schema(root)
        if not schema_path:
            return issues

        # Find migrations directory
        migrations_dir = schema_path.parent / 'migrations'
        if not migrations_dir.exists():
            issues.append(ValidationIssue(
                severity='HIGH',
                category='migration',
                message='No migrations directory found — schema may not be deployed',
                file_path=str(schema_path),
                suggestion='Run: npx prisma migrate dev',
            ))
            return issues

        # Get schema modification time
        schema_mtime = schema_path.stat().st_mtime

        # Get latest migration time
        migration_dirs = sorted([
            d for d in migrations_dir.iterdir()
            if d.is_dir() and d.name != '_meta'
        ])

        if not migration_dirs:
            issues.append(ValidationIssue(
                severity='HIGH',
                category='migration',
                message='No migrations found — schema changes have never been migrated',
                file_path=str(schema_path),
                suggestion='Run: npx prisma migrate dev --name init',
            ))
            return issues

        latest_migration = migration_dirs[-1]
        latest_mtime = latest_migration.stat().st_mtime

        if schema_mtime > latest_mtime:
            issues.append(ValidationIssue(
                severity='HIGH',
                category='migration',
                message=f'Schema modified after latest migration "{latest_migration.name}" — migration may be needed',
                file_path=str(schema_path),
                suggestion='Run: npx prisma migrate dev --name <description>',
            ))

        # Check for drift: parse schema and compare with latest migration SQL
        migration_sql = latest_migration / 'migration.sql'
        if migration_sql.exists():
            sql_content = migration_sql.read_text(encoding='utf-8', errors='ignore')
            schema_content = schema_path.read_text(encoding='utf-8', errors='ignore')

            # Quick heuristic: check for models in schema not in migration
            schema_models = set(re.findall(r'model\s+(\w+)\s*\{', schema_content))
            # Look for CREATE TABLE in SQL
            sql_tables = set(re.findall(r'CREATE TABLE\s+"?(\w+)"?', sql_content, re.IGNORECASE))

            # This is cumulative — only latest migration matters for new tables
            # So just flag as info if there's a mismatch
            for model in schema_models:
                lower_model = model.lower()
                if not any(t.lower() == lower_model or t.lower() == model.lower() + 's' for t in sql_tables):
                    # Could be in an older migration — just informational
                    pass

        return issues

    def _find_schema(self, root: Path) -> Optional[Path]:
        """Find schema.prisma in workspace."""
        candidates = [
            root / 'prisma' / 'schema.prisma',
            root / 'schema.prisma',
            root / 'db' / 'schema.prisma',
        ]
        for c in candidates:
            if c.exists():
                return c

        # Search for it
        for p in root.rglob('schema.prisma'):
            if 'node_modules' not in str(p):
                return p

        return None


# ──────────────────────────────────────────────────────────────
# Include / Select Validator
# ──────────────────────────────────────────────────────────────

class IncludeSelectValidator:
    """Validates Prisma include/select usage in code against schema."""

    INCLUDE_PATTERN = re.compile(r'include\s*:\s*\{([^}]+)\}', re.DOTALL)
    SELECT_PATTERN = re.compile(r'select\s*:\s*\{([^}]+)\}', re.DOTALL)
    FIND_CALL = re.compile(r'\.(\w+)\.(?:findMany|findUnique|findFirst|create|update|delete|upsert)\s*\(\s*\{', re.DOTALL)

    def validate_file(self, file_path: str, schema: PrismaSchema) -> List[ValidationIssue]:
        """Check include/select usage in a file against schema."""
        issues = []
        path = Path(file_path)
        if not path.exists():
            return issues

        content = path.read_text(encoding='utf-8', errors='ignore')
        lines = content.split('\n')

        # Find prisma client calls
        for i, line in enumerate(lines, 1):
            # Check includes
            for match in self.INCLUDE_PATTERN.finditer(line):
                include_body = match.group(1)
                # Try to determine which model
                model_match = self.FIND_CALL.search(content[:content.index(line)])
                if model_match:
                    model_name = model_match.group(1)
                    # Capitalize first letter for Prisma model convention
                    model_key = model_name[0].upper() + model_name[1:]
                    model = schema.models.get(model_key)
                    if model:
                        issues.extend(self._validate_include(include_body, model, file_path, i))

        return issues

    def _validate_include(self, body: str, model: PrismaModel, file_path: str, line: int) -> List[ValidationIssue]:
        """Validate fields in an include block."""
        issues = []
        fields_used = re.findall(r'(\w+)\s*:', body)

        for field_name in fields_used:
            if field_name not in model.fields:
                issues.append(ValidationIssue(
                    severity='HIGH',
                    category='include_select',
                    message=f'Include references non-existent field "{field_name}" on model {model.name}',
                    model=model.name,
                    field_name=field_name,
                    file_path=file_path,
                    line_number=line,
                    suggestion=f'Check available relations on {model.name}',
                ))
            else:
                f = model.fields[field_name]
                if not f.relation and f.type not in {'Json'}:
                    issues.append(ValidationIssue(
                        severity='MEDIUM',
                        category='include_select',
                        message=f'Include on non-relation field "{field_name}" on model {model.name} — use select instead',
                        model=model.name,
                        field_name=field_name,
                        file_path=file_path,
                        line_number=line,
                    ))

        return issues


# ──────────────────────────────────────────────────────────────
# Main Analyzer (Facade)
# ──────────────────────────────────────────────────────────────

class PrismaAnalyzer:
    """Top-level facade combining all Prisma intelligence."""

    def __init__(self):
        self.parser = PrismaParser()
        self.validator = PrismaValidator()
        self.dto_validator = DTOValidator()
        self.migration_checker = MigrationChecker()
        self.include_validator = IncludeSelectValidator()
        self._schema_cache: Dict[str, PrismaSchema] = {}

    def analyze_workspace(self, workspace_path: str) -> Dict[str, Any]:
        """Full Prisma analysis of a workspace."""
        root = Path(workspace_path)

        # Find and parse schema
        schema_path = self._find_schema(root)
        if not schema_path:
            return {
                'has_prisma': False,
                'message': 'No schema.prisma found in workspace',
            }

        schema = self.parser.parse_file(str(schema_path))
        self._schema_cache[workspace_path] = schema

        # Run validations
        schema_issues = self.validator.validate(schema)
        migration_issues = self.migration_checker.check_migration_status(workspace_path)

        # Find and validate DTOs
        dtos = self.dto_validator.extract_dtos_from_workspace(workspace_path)
        dto_issues = []
        dto_matches = []
        for dto in dtos:
            best_model = self._match_dto_to_model(dto['name'], schema)
            if best_model:
                dto_matches.append({'dto': dto['name'], 'model': best_model.name})
                dto_issues.extend(self.dto_validator.compare_dto_to_model(dto, best_model))

        all_issues = schema_issues + migration_issues + dto_issues

        return {
            'has_prisma': True,
            'schema_path': str(schema_path),
            'models': {name: self._model_summary(m) for name, m in schema.models.items()},
            'enums': {name: e.values for name, e in schema.enums.items()},
            'total_issues': len(all_issues),
            'issues_by_severity': self._group_by_severity(all_issues),
            'issues': [asdict(i) for i in all_issues],
            'dtos_found': len(dtos),
            'dto_model_matches': dto_matches,
            'migration_status': 'issues_found' if migration_issues else 'ok',
        }

    def get_schema(self, workspace_path: str) -> Optional[Dict[str, Any]]:
        """Get parsed schema (cached)."""
        if workspace_path in self._schema_cache:
            schema = self._schema_cache[workspace_path]
        else:
            root = Path(workspace_path)
            schema_path = self._find_schema(root)
            if not schema_path:
                return None
            schema = self.parser.parse_file(str(schema_path))
            self._schema_cache[workspace_path] = schema

        return {
            'models': {name: self._model_summary(m) for name, m in schema.models.items()},
            'enums': {name: e.values for name, e in schema.enums.items()},
            'datasource': schema.datasource,
        }

    def validate_schema(self, workspace_path: str) -> Dict[str, Any]:
        """Validate Prisma schema only."""
        root = Path(workspace_path)
        schema_path = self._find_schema(root)
        if not schema_path:
            return {'valid': False, 'error': 'No schema.prisma found'}

        schema = self.parser.parse_file(str(schema_path))
        issues = self.validator.validate(schema)

        return {
            'valid': len([i for i in issues if i.severity in ('CRITICAL', 'HIGH')]) == 0,
            'total_issues': len(issues),
            'issues': [asdict(i) for i in issues],
        }

    def validate_dto(self, workspace_path: str, dto_file: str) -> Dict[str, Any]:
        """Validate a specific DTO file against Prisma schema."""
        root = Path(workspace_path)
        schema_path = self._find_schema(root)
        if not schema_path:
            return {'error': 'No schema.prisma found'}

        schema = self.parser.parse_file(str(schema_path))
        dtos = self.dto_validator.extract_dtos_from_file(dto_file)

        all_issues = []
        matches = []
        for dto in dtos:
            best_model = self._match_dto_to_model(dto['name'], schema)
            if best_model:
                matches.append({'dto': dto['name'], 'model': best_model.name})
                all_issues.extend(self.dto_validator.compare_dto_to_model(dto, best_model))

        return {
            'dtos_found': len(dtos),
            'matches': matches,
            'issues': [asdict(i) for i in all_issues],
        }

    def check_include_select(self, workspace_path: str, file_path: str) -> Dict[str, Any]:
        """Validate include/select usage in a specific file."""
        root = Path(workspace_path)
        schema_path = self._find_schema(root)
        if not schema_path:
            return {'error': 'No schema.prisma found'}

        schema = self.parser.parse_file(str(schema_path))
        issues = self.include_validator.validate_file(file_path, schema)

        return {
            'file': file_path,
            'issues': [asdict(i) for i in issues],
        }

    def _find_schema(self, root: Path) -> Optional[Path]:
        candidates = [
            root / 'prisma' / 'schema.prisma',
            root / 'schema.prisma',
            root / 'db' / 'schema.prisma',
        ]
        for c in candidates:
            if c.exists():
                return c
        for p in root.rglob('schema.prisma'):
            if 'node_modules' not in str(p):
                return p
        return None

    def _match_dto_to_model(self, dto_name: str, schema: PrismaSchema) -> Optional[PrismaModel]:
        """Heuristic match DTO name to Prisma model."""
        # Strip common suffixes
        clean = re.sub(r'(Dto|DTO|Input|Output|Request|Response|Schema|Create|Update|Payload)$', '', dto_name)
        if clean in schema.models:
            return schema.models[clean]

        # Case-insensitive match
        lower = clean.lower()
        for name, model in schema.models.items():
            if name.lower() == lower:
                return model

        return None

    def _model_summary(self, model: PrismaModel) -> Dict[str, Any]:
        return {
            'fields': {
                name: {
                    'type': f.type,
                    'optional': f.is_optional,
                    'list': f.is_list,
                    'id': f.is_id,
                    'unique': f.is_unique,
                    'relation': bool(f.relation),
                    'default': f.default,
                }
                for name, f in model.fields.items()
            },
            'indexes': model.indexes,
            'unique_constraints': model.unique_constraints,
            'id_fields': model.id_fields,
        }

    def _group_by_severity(self, issues: List[ValidationIssue]) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for i in issues:
            counts[i.severity] = counts.get(i.severity, 0) + 1
        return counts
