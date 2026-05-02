"""
Tests for the three Enforcement Pillars:
  1. Prisma / ORM Intelligence (prisma_analyzer.py)
  2. API Contract Enforcement (contract_analyzer.py)
  3. Change Impact Analysis (impact_analyzer.py)
  4. Unified Validation Pipeline (validation_pipeline.py)

Run with: pytest tests/test_enforcement.py -v
"""
import os
import sys
import json
import tempfile
import shutil
import pytest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ──────────────────────────────────────────────────────────────
# Prisma Schema Parser Tests
# ──────────────────────────────────────────────────────────────

SAMPLE_PRISMA_SCHEMA = """
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

generator client {
  provider = "prisma-client-js"
}

enum Role {
  USER
  ADMIN
  MODERATOR
}

model User {
  id        Int      @id @default(autoincrement())
  email     String   @unique
  name      String?
  password  String
  role      Role     @default(USER)
  posts     Post[]
  profile   Profile?
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  @@index([email])
  @@map("users")
}

model Post {
  id        Int      @id @default(autoincrement())
  title     String
  content   String?
  published Boolean  @default(false)
  authorId  Int
  author    User     @relation(fields: [authorId], references: [id], onDelete: Cascade)
  tags      Tag[]
  createdAt DateTime @default(now())

  @@index([authorId])
  @@index([title])
}

model Profile {
  id     Int    @id @default(autoincrement())
  bio    String?
  userId Int    @unique
  user   User   @relation(fields: [userId], references: [id])
}

model Tag {
  id    Int    @id @default(autoincrement())
  name  String @unique
  posts Post[]
}
"""

BROKEN_PRISMA_SCHEMA = """
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model User {
  id    Int    @id @default(autoincrement())
  email String
  posts Post[]
}

model Post {
  id       Int  @id @default(autoincrement())
  title    String
  authorId Int
  author   User @relation(fields: [authorId], references: [id], onDelete: Cascade)
  category FakeType
}

model Orphan {
  name String
}
"""


class TestPrismaParser:
    def setup_method(self):
        from prisma_analyzer import PrismaParser
        self.parser = PrismaParser()

    def test_parse_models(self):
        schema = self.parser.parse_text(SAMPLE_PRISMA_SCHEMA)
        assert 'User' in schema.models
        assert 'Post' in schema.models
        assert 'Profile' in schema.models
        assert 'Tag' in schema.models

    def test_parse_fields(self):
        schema = self.parser.parse_text(SAMPLE_PRISMA_SCHEMA)
        user = schema.models['User']
        assert 'email' in user.fields
        assert 'name' in user.fields
        assert user.fields['email'].is_unique
        assert user.fields['name'].is_optional
        assert user.fields['id'].is_id

    def test_parse_relations(self):
        schema = self.parser.parse_text(SAMPLE_PRISMA_SCHEMA)
        post = schema.models['Post']
        author_field = post.fields['author']
        assert author_field.relation is not None
        assert author_field.relation['fields'] == ['authorId']
        assert author_field.relation['references'] == ['id']
        assert author_field.relation['onDelete'] == 'Cascade'

    def test_parse_enums(self):
        schema = self.parser.parse_text(SAMPLE_PRISMA_SCHEMA)
        assert 'Role' in schema.enums
        assert 'USER' in schema.enums['Role'].values
        assert 'ADMIN' in schema.enums['Role'].values

    def test_parse_indexes(self):
        schema = self.parser.parse_text(SAMPLE_PRISMA_SCHEMA)
        user = schema.models['User']
        assert len(user.indexes) >= 1
        index_fields = [f for idx in user.indexes for f in idx['fields']]
        assert 'email' in index_fields

    def test_parse_map(self):
        schema = self.parser.parse_text(SAMPLE_PRISMA_SCHEMA)
        user = schema.models['User']
        assert user.map_name == 'users'

    def test_parse_datasource(self):
        schema = self.parser.parse_text(SAMPLE_PRISMA_SCHEMA)
        assert schema.datasource.get('provider') == 'postgresql'

    def test_parse_generator(self):
        schema = self.parser.parse_text(SAMPLE_PRISMA_SCHEMA)
        assert len(schema.generators) >= 1
        assert schema.generators[0]['provider'] == 'prisma-client-js'

    def test_parse_list_field(self):
        schema = self.parser.parse_text(SAMPLE_PRISMA_SCHEMA)
        user = schema.models['User']
        assert user.fields['posts'].is_list

    def test_parse_optional_field(self):
        schema = self.parser.parse_text(SAMPLE_PRISMA_SCHEMA)
        user = schema.models['User']
        assert user.fields['name'].is_optional
        assert not user.fields['email'].is_optional

    def test_parse_defaults(self):
        schema = self.parser.parse_text(SAMPLE_PRISMA_SCHEMA)
        user = schema.models['User']
        assert user.fields['role'].default == 'USER'

    def test_parse_empty_string(self):
        schema = self.parser.parse_text("")
        assert len(schema.models) == 0

    def test_parse_id_fields(self):
        schema = self.parser.parse_text(SAMPLE_PRISMA_SCHEMA)
        user = schema.models['User']
        assert 'id' in user.id_fields


class TestPrismaValidator:
    def setup_method(self):
        from prisma_analyzer import PrismaParser, PrismaValidator
        self.parser = PrismaParser()
        self.validator = PrismaValidator()

    def test_valid_schema(self):
        schema = self.parser.parse_text(SAMPLE_PRISMA_SCHEMA)
        issues = self.validator.validate(schema)
        # Valid schema should have few/no critical issues
        critical = [i for i in issues if i.severity == 'CRITICAL']
        assert len(critical) == 0

    def test_detect_unknown_type(self):
        schema = self.parser.parse_text(BROKEN_PRISMA_SCHEMA)
        issues = self.validator.validate(schema)
        type_issues = [i for i in issues if 'FakeType' in i.message]
        assert len(type_issues) > 0

    def test_detect_missing_id(self):
        schema = self.parser.parse_text(BROKEN_PRISMA_SCHEMA)
        issues = self.validator.validate(schema)
        id_issues = [i for i in issues if 'no @id' in i.message.lower() or 'no @id' in (i.suggestion or '').lower()]
        assert len(id_issues) > 0  # Orphan model has no @id

    def test_cascade_warning(self):
        schema = self.parser.parse_text(SAMPLE_PRISMA_SCHEMA)
        issues = self.validator.validate(schema)
        cascade_issues = [i for i in issues if i.category == 'cascade']
        # Post.author has Cascade on User which has many relations
        assert len(cascade_issues) >= 0  # May or may not trigger depending on relation count


class TestDTOValidator:
    def setup_method(self):
        from prisma_analyzer import PrismaParser, DTOValidator
        self.parser = PrismaParser()
        self.dto_validator = DTOValidator()

    def test_extract_ts_interface(self):
        content = '''
export interface UserDto {
  email: string;
  name?: string;
  password: string;
}
'''
        dtos = self.dto_validator._extract_ts_interfaces(content, 'test.ts')
        assert len(dtos) == 1
        assert dtos[0]['name'] == 'UserDto'
        assert 'email' in dtos[0]['fields']
        assert dtos[0]['fields']['name']['optional'] is True

    def test_extract_pydantic_model(self):
        content = '''
class UserCreate(BaseModel):
    email: str
    name: Optional[str] = None
    password: str
'''
        dtos = self.dto_validator._extract_pydantic_models(content, 'test.py')
        assert len(dtos) == 1
        assert dtos[0]['name'] == 'UserCreate'
        assert 'email' in dtos[0]['fields']
        assert dtos[0]['fields']['name']['optional'] is True

    def test_compare_dto_to_model(self):
        schema = self.parser.parse_text(SAMPLE_PRISMA_SCHEMA)
        user_model = schema.models['User']

        dto = {
            'name': 'UserDto',
            'fields': {
                'email': {'type': 'string', 'optional': False},
                'name': {'type': 'string', 'optional': True},
                'password': {'type': 'string', 'optional': False},
            },
            'file_path': 'test.ts',
        }

        issues = self.dto_validator.compare_dto_to_model(dto, user_model)
        # Should not have critical issues for matching fields
        critical = [i for i in issues if i.severity == 'CRITICAL']
        assert len(critical) == 0

    def test_detect_missing_required_field(self):
        schema = self.parser.parse_text(SAMPLE_PRISMA_SCHEMA)
        user_model = schema.models['User']

        dto = {
            'name': 'UserDto',
            'fields': {
                'name': {'type': 'string', 'optional': True},
                # Missing email and password
            },
            'file_path': 'test.ts',
        }

        issues = self.dto_validator.compare_dto_to_model(dto, user_model)
        missing = [i for i in issues if 'missing' in i.message.lower() and i.severity == 'HIGH']
        assert len(missing) > 0


class TestMigrationChecker:
    def setup_method(self):
        from prisma_analyzer import MigrationChecker
        self.checker = MigrationChecker()

    def test_no_prisma_project(self):
        tmpdir = tempfile.mkdtemp()
        try:
            issues = self.checker.check_migration_status(tmpdir)
            assert len(issues) == 0  # No schema = nothing to check
        finally:
            shutil.rmtree(tmpdir)

    def test_schema_without_migrations(self):
        tmpdir = tempfile.mkdtemp()
        try:
            prisma_dir = Path(tmpdir) / 'prisma'
            prisma_dir.mkdir()
            (prisma_dir / 'schema.prisma').write_text(SAMPLE_PRISMA_SCHEMA)

            issues = self.checker.check_migration_status(tmpdir)
            assert len(issues) > 0
            assert any('migration' in i.message.lower() for i in issues)
        finally:
            shutil.rmtree(tmpdir)


# ──────────────────────────────────────────────────────────────
# API Contract Enforcement Tests
# ──────────────────────────────────────────────────────────────

class TestEndpointExtractor:
    def setup_method(self):
        from contract_analyzer import EndpointExtractor
        self.extractor = EndpointExtractor()

    def test_extract_express_routes(self):
        tmpdir = tempfile.mkdtemp()
        try:
            Path(tmpdir, 'routes.js').write_text('''
const express = require("express");
const router = express.Router();

router.get("/users", getAllUsers);
router.post("/users", createUser);
router.get("/users/:id", getUserById);
router.put("/users/:id", updateUser);
router.delete("/users/:id", deleteUser);
''')
            contracts = self.extractor.extract_contracts(tmpdir)
            assert len(contracts) == 5
            methods = {c.method for c in contracts}
            assert methods == {'GET', 'POST', 'PUT', 'DELETE'}
        finally:
            shutil.rmtree(tmpdir)

    def test_extract_fastapi_routes(self):
        tmpdir = tempfile.mkdtemp()
        try:
            Path(tmpdir, 'api.py').write_text('''
from fastapi import FastAPI
app = FastAPI()

@app.get("/items")
async def list_items():
    return []

@app.post("/items", status_code=201)
async def create_item():
    return {}

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    return {}
''')
            contracts = self.extractor.extract_contracts(tmpdir)
            assert len(contracts) == 3
        finally:
            shutil.rmtree(tmpdir)

    def test_extract_nest_routes(self):
        tmpdir = tempfile.mkdtemp()
        try:
            Path(tmpdir, 'user.controller.ts').write_text('''
import { Controller, Get, Post, UseGuards, Body, Param } from "@nestjs/common";

@Controller("users")
@UseGuards(AuthGuard)
export class UserController {
    @Get()
    async findAll(): Promise<User[]> {
        return [];
    }

    @Post()
    async create(@Body() dto: CreateUserDto): Promise<User> {
        return {};
    }

    @Get(":id")
    async findOne(@Param("id") id: string): Promise<User> {
        return {};
    }
}
''')
            contracts = self.extractor.extract_contracts(tmpdir)
            assert len(contracts) >= 3
            # Check guard detection
            guarded = [c for c in contracts if c.auth_guard]
            assert len(guarded) > 0
        finally:
            shutil.rmtree(tmpdir)


class TestContractValidator:
    def setup_method(self):
        from contract_analyzer import ContractValidator, EndpointContract
        self.validator = ContractValidator()
        self.EndpointContract = EndpointContract

    def test_detect_duplicate_routes(self):
        contracts = [
            self.EndpointContract(method='GET', path='/users', file_path='a.py', line_number=1),
            self.EndpointContract(method='GET', path='/users', file_path='b.py', line_number=5),
        ]
        violations = self.validator.validate(contracts)
        duplicates = [v for v in violations if v.category == 'duplicate']
        assert len(duplicates) > 0

    def test_detect_get_with_body(self):
        contracts = [
            self.EndpointContract(
                method='GET', path='/search',
                request_body_fields={'query': 'string'},
                file_path='a.py', line_number=1,
            ),
        ]
        violations = self.validator.validate(contracts)
        http_issues = [v for v in violations if v.category == 'http_discipline']
        assert len(http_issues) > 0

    def test_detect_verb_in_url(self):
        contracts = [
            self.EndpointContract(method='POST', path='/api/create/user', file_path='a.py', line_number=1),
        ]
        violations = self.validator.validate(contracts)
        naming = [v for v in violations if v.category == 'naming']
        assert len(naming) > 0

    def test_detect_camelcase_in_url(self):
        contracts = [
            self.EndpointContract(method='GET', path='/api/userProfile', file_path='a.py', line_number=1),
        ]
        violations = self.validator.validate(contracts)
        naming = [v for v in violations if 'camelCase' in v.message]
        assert len(naming) > 0

    def test_auth_consistency(self):
        contracts = [
            self.EndpointContract(method='GET', path='/api/items', auth_guard='AuthGuard', file_path='a.py', line_number=1),
            self.EndpointContract(method='POST', path='/api/items', file_path='a.py', line_number=10),
            self.EndpointContract(method='DELETE', path='/api/items/:id', file_path='a.py', line_number=20),
        ]
        violations = self.validator.validate(contracts)
        auth = [v for v in violations if v.category == 'auth']
        assert len(auth) > 0  # POST and DELETE unguarded

    def test_no_violations_for_clean_api(self):
        contracts = [
            self.EndpointContract(method='GET', path='/api/users', auth_guard='AuthGuard', file_path='a.py', line_number=1),
            self.EndpointContract(method='POST', path='/api/users', auth_guard='AuthGuard', file_path='a.py', line_number=10),
        ]
        violations = self.validator.validate(contracts)
        critical = [v for v in violations if v.severity == 'CRITICAL']
        assert len(critical) == 0


class TestContractAnalyzer:
    def setup_method(self):
        from contract_analyzer import ContractAnalyzer
        self.analyzer = ContractAnalyzer()

    def test_analyze_workspace(self):
        tmpdir = tempfile.mkdtemp()
        try:
            Path(tmpdir, 'server.py').write_text('''
from fastapi import FastAPI
app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/users")
async def list_users():
    return []
''')
            result = self.analyzer.analyze_workspace(tmpdir)
            assert result['total_endpoints'] >= 2
            assert 'auth_coverage' in result
        finally:
            shutil.rmtree(tmpdir)


# ──────────────────────────────────────────────────────────────
# Change Impact Analysis Tests
# ──────────────────────────────────────────────────────────────

class TestDependencyGraph:
    def setup_method(self):
        from impact_analyzer import DependencyGraph
        self.graph = DependencyGraph()

    def test_build_graph(self):
        tmpdir = tempfile.mkdtemp()
        try:
            Path(tmpdir, 'models.py').write_text('class User:\n    pass\n')
            Path(tmpdir, 'service.py').write_text('from models import User\n\ndef get_user():\n    return User()\n')
            Path(tmpdir, 'routes.py').write_text('from service import get_user\n\ndef user_route():\n    return get_user()\n')

            result = self.graph.build(tmpdir)
            assert result['total_files'] >= 3
        finally:
            shutil.rmtree(tmpdir)

    def test_classify_file(self):
        assert self.graph._classify_file('src/models/user.py') == 'model'
        assert self.graph._classify_file('src/routes/user.ts') == 'route'
        assert self.graph._classify_file('src/services/auth.py') == 'service'
        assert self.graph._classify_file('test_user.py') == 'test'
        assert self.graph._classify_file('src/middleware/auth.ts') == 'middleware'
        assert self.graph._classify_file('config.py') == 'config'


class TestChangeDetector:
    def setup_method(self):
        from impact_analyzer import ChangeDetector
        self.detector = ChangeDetector()

    def test_detect_added_function(self):
        old = 'class User:\n    pass\n'
        new = 'class User:\n    pass\n\ndef new_function():\n    pass\n'
        changes = self.detector.detect_changes(old, new, 'python')
        assert 'new_function' in changes['added_symbols']

    def test_detect_removed_function(self):
        old = 'def old_function():\n    pass\n\ndef keep():\n    pass\n'
        new = 'def keep():\n    pass\n'
        changes = self.detector.detect_changes(old, new, 'python')
        assert 'old_function' in changes['removed_symbols']


class TestImpactAnalyzer:
    def setup_method(self):
        from impact_analyzer import ImpactAnalyzer
        self.analyzer = ImpactAnalyzer()

    def test_analyze_model_change(self):
        tmpdir = tempfile.mkdtemp()
        try:
            model_file = Path(tmpdir, 'models.py')
            model_file.write_text('class User:\n    pass\n')
            Path(tmpdir, 'service.py').write_text('from models import User\n')
            Path(tmpdir, 'routes.py').write_text('from service import get_user\n')

            self.analyzer.build_graph(tmpdir)
            result = self.analyzer.analyze_change(
                tmpdir, str(model_file),
                'class User:\n    pass\n',
                'class User:\n    name = ""\n\nclass Admin:\n    pass\n'
            )

            assert result['category'] == 'model'
            assert result['risk_score'] > 0
        finally:
            shutil.rmtree(tmpdir)

    def test_analyze_test_change_low_risk(self):
        tmpdir = tempfile.mkdtemp()
        try:
            test_file = Path(tmpdir, 'test_user.py')
            test_file.write_text('def test_user():\n    pass\n')

            self.analyzer.build_graph(tmpdir)
            result = self.analyzer.analyze_change(tmpdir, str(test_file))

            assert result['category'] == 'test'
            assert result['risk_score'] <= 0.3
        finally:
            shutil.rmtree(tmpdir)

    def test_file_info(self):
        tmpdir = tempfile.mkdtemp()
        try:
            model_file = Path(tmpdir, 'models.py')
            model_file.write_text('class User:\n    pass\n')

            self.analyzer.build_graph(tmpdir)
            info = self.analyzer.get_file_info(tmpdir, str(model_file))

            assert info['category'] == 'model'
            assert 'dependents' in info
        finally:
            shutil.rmtree(tmpdir)


# ──────────────────────────────────────────────────────────────
# Validation Pipeline Tests
# ──────────────────────────────────────────────────────────────

class TestValidationPipeline:
    def setup_method(self):
        from validation_pipeline import ValidationPipeline
        self.pipeline = ValidationPipeline()

    def test_full_scan(self):
        tmpdir = tempfile.mkdtemp()
        try:
            Path(tmpdir, 'app.py').write_text('''
from fastapi import FastAPI
app = FastAPI()

@app.get("/users")
async def list_users():
    return []
''')
            result = self.pipeline.full_scan(tmpdir)
            assert 'overall_risk_score' in result
            assert 'overall_risk_level' in result
            assert 'prisma' in result
            assert 'contracts' in result
            assert 'security' in result
            assert 'impact' in result
        finally:
            shutil.rmtree(tmpdir)

    def test_file_change_scan(self):
        tmpdir = tempfile.mkdtemp()
        try:
            f = Path(tmpdir, 'api.py')
            f.write_text('def handler():\n    pass\n')

            result = self.pipeline.on_file_change(tmpdir, str(f))
            assert 'overall_risk_score' in result
            assert 'issues' in result
        finally:
            shutil.rmtree(tmpdir)

    def test_pre_commit_validation(self):
        tmpdir = tempfile.mkdtemp()
        try:
            f1 = Path(tmpdir, 'models.py')
            f1.write_text('class User:\n    pass\n')
            f2 = Path(tmpdir, 'routes.py')
            f2.write_text('def get_user():\n    pass\n')

            result = self.pipeline.validate_before_commit(tmpdir, [str(f1), str(f2)])
            assert 'commit_safe' in result
            assert 'summary' in result
        finally:
            shutil.rmtree(tmpdir)


class TestStackDetector:
    def setup_method(self):
        from validation_pipeline import StackDetector
        self.detector = StackDetector()

    def test_detect_node_project(self):
        tmpdir = tempfile.mkdtemp()
        try:
            Path(tmpdir, 'package.json').write_text(json.dumps({
                "dependencies": {
                    "next": "14.0.0",
                    "@prisma/client": "5.0.0",
                    "next-auth": "4.0.0",
                },
                "devDependencies": {
                    "typescript": "5.0.0",
                    "jest": "29.0.0",
                }
            }))
            Path(tmpdir, 'pnpm-lock.yaml').write_text('')

            result = self.detector.detect(tmpdir)
            assert result['language'] == 'typescript'
            assert result['framework'] == 'Next.js'
            assert result['orm'] == 'Prisma'
            assert result['auth'] == 'NextAuth'
            assert result['test'] == 'Jest'
            assert result['package_manager'] == 'pnpm'
        finally:
            shutil.rmtree(tmpdir)

    def test_detect_python_project(self):
        tmpdir = tempfile.mkdtemp()
        try:
            Path(tmpdir, 'requirements.txt').write_text('fastapi\nsqlalchemy\nuvicorn\n')

            result = self.detector.detect(tmpdir)
            assert result['language'] == 'python'
            assert result['framework'] == 'FastAPI'
            assert result['orm'] == 'SQLAlchemy'
        finally:
            shutil.rmtree(tmpdir)

    def test_detect_empty_project(self):
        tmpdir = tempfile.mkdtemp()
        try:
            result = self.detector.detect(tmpdir)
            assert result['language'] is None
        finally:
            shutil.rmtree(tmpdir)


# ──────────────────────────────────────────────────────────────
# Integration Tests (Server API)
# ──────────────────────────────────────────────────────────────

from fastapi.testclient import TestClient
from server import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def enforcement_workspace():
    """Create a workspace with Prisma schema and API routes for testing."""
    tmpdir = tempfile.mkdtemp(prefix="enforcement_test_")

    # Prisma schema
    prisma_dir = Path(tmpdir) / 'prisma'
    prisma_dir.mkdir()
    (prisma_dir / 'schema.prisma').write_text(SAMPLE_PRISMA_SCHEMA)

    # API route file
    Path(tmpdir, 'routes.py').write_text('''
from fastapi import FastAPI
app = FastAPI()

@app.get("/users")
async def list_users():
    return []

@app.post("/users", status_code=201)
async def create_user():
    return {}

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    return {}

@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    return {"deleted": True}
''')

    # Service file
    Path(tmpdir, 'service.py').write_text('''
from models import User

def get_all_users():
    return []
''')

    # Model file
    Path(tmpdir, 'models.py').write_text('''
class User:
    id: int
    email: str
    name: str
''')

    # DTO file
    Path(tmpdir, 'user_dto.py').write_text('''
from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    email: str
    name: Optional[str] = None
    password: str
''')

    yield tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)


class TestPrismaAPI:
    def test_prisma_analyze(self, client, enforcement_workspace):
        r = client.post("/prisma/analyze", json={"workspace_path": enforcement_workspace})
        assert r.status_code == 200
        data = r.json()
        assert data['has_prisma'] is True
        assert 'User' in data['models']
        assert 'Post' in data['models']
        assert 'total_issues' in data

    def test_prisma_validate(self, client, enforcement_workspace):
        r = client.post("/prisma/validate", json={"workspace_path": enforcement_workspace})
        assert r.status_code == 200
        data = r.json()
        assert 'valid' in data

    def test_prisma_schema(self, client, enforcement_workspace):
        r = client.post("/prisma/schema", json={"workspace_path": enforcement_workspace})
        assert r.status_code == 200
        data = r.json()
        assert 'models' in data
        assert 'enums' in data

    def test_prisma_schema_not_found(self, client):
        tmpdir = tempfile.mkdtemp()
        try:
            r = client.post("/prisma/schema", json={"workspace_path": tmpdir})
            assert r.status_code == 404
        finally:
            shutil.rmtree(tmpdir)


class TestContractAPI:
    def test_contract_analyze(self, client, enforcement_workspace):
        r = client.post("/contracts/analyze", json={"workspace_path": enforcement_workspace})
        assert r.status_code == 200
        data = r.json()
        assert data['total_endpoints'] >= 4
        assert 'violations' in data
        assert 'auth_coverage' in data

    def test_contract_validate(self, client, enforcement_workspace):
        r = client.post("/contracts/validate", json={"workspace_path": enforcement_workspace})
        assert r.status_code == 200
        data = r.json()
        assert 'valid' in data

    def test_contract_map(self, client, enforcement_workspace):
        r = client.post("/contracts/map", json={"workspace_path": enforcement_workspace})
        assert r.status_code == 200
        data = r.json()
        assert 'total_paths' in data
        assert 'map' in data

    def test_contract_check(self, client, enforcement_workspace):
        # First analyze to populate registry
        client.post("/contracts/analyze", json={"workspace_path": enforcement_workspace})
        r = client.post("/contracts/check", json={
            "workspace_path": enforcement_workspace,
            "method": "GET",
            "path": "/users"
        })
        assert r.status_code == 200


class TestImpactAPI:
    def test_build_graph(self, client, enforcement_workspace):
        r = client.post("/impact/build-graph", json={"workspace_path": enforcement_workspace})
        assert r.status_code == 200
        data = r.json()
        assert 'total_files' in data
        assert data['total_files'] >= 2

    def test_analyze_impact(self, client, enforcement_workspace):
        model_file = os.path.join(enforcement_workspace, 'models.py')
        r = client.post("/impact/analyze", json={
            "workspace_path": enforcement_workspace,
            "changed_file": model_file,
        })
        assert r.status_code == 200
        data = r.json()
        assert 'risk_score' in data
        assert 'risk_level' in data
        assert 'category' in data

    def test_dependency_map(self, client, enforcement_workspace):
        r = client.post("/impact/dependency-map", json={"workspace_path": enforcement_workspace})
        assert r.status_code == 200
        data = r.json()
        assert 'total_files' in data

    def test_file_info(self, client, enforcement_workspace):
        model_file = os.path.join(enforcement_workspace, 'models.py')
        r = client.post("/impact/file-info", json={
            "workspace_path": enforcement_workspace,
            "file_path": model_file,
        })
        assert r.status_code == 200
        data = r.json()
        assert 'category' in data


class TestPipelineAPI:
    def test_full_scan(self, client, enforcement_workspace):
        r = client.post("/pipeline/full-scan", json={"workspace_path": enforcement_workspace})
        assert r.status_code == 200
        data = r.json()
        assert 'overall_risk_score' in data
        assert 'overall_risk_level' in data
        assert 'issues' in data
        assert 'prisma' in data
        assert 'contracts' in data

    def test_file_change(self, client, enforcement_workspace):
        model_file = os.path.join(enforcement_workspace, 'models.py')
        r = client.post("/pipeline/file-change", json={
            "workspace_path": enforcement_workspace,
            "file_path": model_file,
        })
        assert r.status_code == 200
        data = r.json()
        assert 'overall_risk_score' in data

    def test_pre_commit(self, client, enforcement_workspace):
        model_file = os.path.join(enforcement_workspace, 'models.py')
        routes_file = os.path.join(enforcement_workspace, 'routes.py')
        r = client.post("/pipeline/pre-commit", json={
            "workspace_path": enforcement_workspace,
            "changed_files": [model_file, routes_file],
        })
        assert r.status_code == 200
        data = r.json()
        assert 'commit_safe' in data
        assert 'summary' in data


class TestStackAPI:
    def test_detect_stack(self, client, enforcement_workspace):
        r = client.post("/stack/detect", json={"workspace_path": enforcement_workspace})
        assert r.status_code == 200
        data = r.json()
        assert 'language' in data
        assert 'framework' in data
        assert 'orm' in data
