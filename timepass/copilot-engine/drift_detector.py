"""
Copilot Engine - Structural Drift Detector
Compares AST snapshots across time to detect breaking structural changes:
  - Fields removed / added / renamed / type-changed
  - Nullability changes
  - Return type changes
  - Route method / path changes
  - Signature changes
  - Dead entity detection

Every detected drift becomes a DriftEvent stored in DB.
Severity auto-assigned based on drift type + entity type.
"""
import logging
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timezone
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# Severity Rules
# ──────────────────────────────────────────────────────────────

DRIFT_SEVERITY = {
    # Model/DTO field changes
    ('model', 'field_removed'):       'CRITICAL',
    ('model', 'type_changed'):        'HIGH',
    ('model', 'nullability_changed'): 'HIGH',
    ('model', 'field_renamed'):       'HIGH',
    ('model', 'field_added'):         'LOW',
    ('dto', 'field_removed'):         'CRITICAL',
    ('dto', 'type_changed'):          'HIGH',
    ('dto', 'field_added'):           'MEDIUM',
    ('dto', 'field_renamed'):         'HIGH',
    ('dto', 'nullability_changed'):   'HIGH',

    # Route changes
    ('route', 'route_method_changed'): 'CRITICAL',
    ('route', 'route_path_changed'):   'CRITICAL',
    ('route', 'signature_changed'):    'HIGH',
    ('route', 'field_removed'):        'HIGH',

    # Service / function changes
    ('service', 'signature_changed'):  'MEDIUM',
    ('service', 'return_type_changed'): 'HIGH',
    ('function', 'signature_changed'): 'MEDIUM',
    ('function', 'return_type_changed'): 'HIGH',

    # Class / type changes
    ('class', 'field_removed'):        'MEDIUM',
    ('class', 'signature_changed'):    'MEDIUM',
    ('type_alias', 'type_changed'):    'HIGH',
    ('enum', 'field_removed'):         'HIGH',
    ('enum', 'field_added'):           'LOW',
}


def _get_severity(entity_type: str, drift_type: str) -> str:
    return DRIFT_SEVERITY.get((entity_type, drift_type), 'MEDIUM')


# ──────────────────────────────────────────────────────────────
# Core Drift Detector
# ──────────────────────────────────────────────────────────────

class DriftDetector:
    """
    Detect structural drift by comparing AST snapshots.
    
    Workflow:
      1. On file change, semantic indexer produces a new AST snapshot
      2. DriftDetector compares new snapshot to stored previous snapshot
      3. Any detected differences → DriftEvent records
      4. Previous snapshot replaced with new one
    """

    def compare_snapshots(self, old_snapshot: Dict[str, Any],
                          new_snapshot: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Compare two AST snapshots of the same file.
        Returns list of drift events (not yet persisted).
        """
        if not old_snapshot or not new_snapshot:
            return []

        # Same hash = no change
        if old_snapshot.get('file_hash') == new_snapshot.get('file_hash'):
            return []

        drifts: List[Dict[str, Any]] = []
        file_path = new_snapshot.get('file_path', '')

        old_entities = {e['name']: e for e in old_snapshot.get('entities', [])}
        new_entities = {e['name']: e for e in new_snapshot.get('entities', [])}

        old_names = set(old_entities.keys())
        new_names = set(new_entities.keys())

        # ── Entity Removed ──
        for name in old_names - new_names:
            old_e = old_entities[name]
            # Try to detect rename (similar entity in new set)
            rename_candidate = self._find_rename_candidate(old_e, new_entities, old_names)
            if rename_candidate:
                drifts.append({
                    'file_path': file_path,
                    'entity_name': name,
                    'drift_type': 'entity_renamed',
                    'old_value': name,
                    'new_value': rename_candidate,
                    'severity': _get_severity(old_e['type'], 'field_renamed'),
                })
            else:
                drifts.append({
                    'file_path': file_path,
                    'entity_name': name,
                    'drift_type': 'entity_removed',
                    'old_value': old_e.get('signature', name),
                    'new_value': None,
                    'severity': 'CRITICAL' if old_e['type'] in ('model', 'dto', 'route') else 'HIGH',
                })

        # ── Entity Added ──
        for name in new_names - old_names:
            new_e = new_entities[name]
            # Only flag if not part of a rename
            if not any(d['drift_type'] == 'entity_renamed' and d['new_value'] == name for d in drifts):
                drifts.append({
                    'file_path': file_path,
                    'entity_name': name,
                    'drift_type': 'entity_added',
                    'old_value': None,
                    'new_value': new_e.get('signature', name),
                    'severity': 'LOW',
                })

        # ── Entity Modified (exists in both) ──
        for name in old_names & new_names:
            old_e = old_entities[name]
            new_e = new_entities[name]
            entity_drifts = self._compare_entity(old_e, new_e, file_path)
            drifts.extend(entity_drifts)

        # ── Import changes ──
        old_imports = set(
            m.get('module', '') for m in old_snapshot.get('imports', [])
        )
        new_imports = set(
            m.get('module', '') for m in new_snapshot.get('imports', [])
        )
        for removed_import in old_imports - new_imports:
            drifts.append({
                'file_path': file_path,
                'entity_name': f"import:{removed_import}",
                'drift_type': 'import_removed',
                'old_value': removed_import,
                'new_value': None,
                'severity': 'LOW',
            })

        return drifts

    def persist_drifts(self, drifts: List[Dict[str, Any]], workspace_path: str,
                       db_session) -> int:
        """Store drift events in DB. Returns count persisted."""
        from models import DriftEvent, Workspace

        ws = db_session.query(Workspace).filter(Workspace.path == workspace_path).first()
        if not ws:
            return 0

        count = 0
        for d in drifts:
            db_session.add(DriftEvent(
                workspace_id=ws.id,
                file_path=d['file_path'],
                entity_name=d.get('entity_name', ''),
                drift_type=d['drift_type'],
                old_value=str(d.get('old_value', '')),
                new_value=str(d.get('new_value', '')),
                severity=d.get('severity', 'MEDIUM'),
                timestamp=datetime.now(timezone.utc),
            ))
            count += 1

        db_session.commit()
        return count

    def update_snapshot(self, file_path: str, new_snapshot: Dict[str, Any],
                        workspace_path: str, db_session) -> None:
        """Replace stored AST snapshot for file."""
        from models import ASTSnapshot, Workspace

        ws = db_session.query(Workspace).filter(Workspace.path == workspace_path).first()
        if not ws:
            return

        # Delete old
        db_session.query(ASTSnapshot).filter(
            ASTSnapshot.workspace_id == ws.id,
            ASTSnapshot.file_path == file_path,
        ).delete()

        # Insert new
        db_session.add(ASTSnapshot(
            workspace_id=ws.id,
            file_path=file_path,
            file_hash=new_snapshot.get('file_hash', ''),
            snapshot=new_snapshot,
            timestamp=datetime.now(timezone.utc),
        ))
        db_session.commit()

    def get_stored_snapshot(self, file_path: str, workspace_path: str,
                            db_session) -> Optional[Dict[str, Any]]:
        """Retrieve last stored snapshot for a file."""
        from models import ASTSnapshot, Workspace

        ws = db_session.query(Workspace).filter(Workspace.path == workspace_path).first()
        if not ws:
            return None

        snap = db_session.query(ASTSnapshot).filter(
            ASTSnapshot.workspace_id == ws.id,
            ASTSnapshot.file_path == file_path,
        ).first()

        return snap.snapshot if snap else None

    def get_unresolved_drifts(self, workspace_path: str, db_session,
                               severity: str = None) -> List[Dict[str, Any]]:
        """Get all unresolved drift events."""
        from models import DriftEvent, Workspace

        ws = db_session.query(Workspace).filter(Workspace.path == workspace_path).first()
        if not ws:
            return []

        q = db_session.query(DriftEvent).filter(
            DriftEvent.workspace_id == ws.id,
            DriftEvent.resolved == False,
        )
        if severity:
            q = q.filter(DriftEvent.severity == severity)

        q = q.order_by(DriftEvent.timestamp.desc())

        return [{
            'id': d.id,
            'file_path': d.file_path,
            'entity_name': d.entity_name,
            'drift_type': d.drift_type,
            'old_value': d.old_value,
            'new_value': d.new_value,
            'severity': d.severity,
            'timestamp': d.timestamp.isoformat() if d.timestamp else '',
        } for d in q.limit(200).all()]

    def get_drift_summary(self, workspace_path: str, db_session) -> Dict[str, Any]:
        """Aggregate drift statistics."""
        from models import DriftEvent, Workspace

        ws = db_session.query(Workspace).filter(Workspace.path == workspace_path).first()
        if not ws:
            return {'total': 0}

        all_drifts = db_session.query(DriftEvent).filter(
            DriftEvent.workspace_id == ws.id,
            DriftEvent.resolved == False,
        ).all()

        by_severity = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        by_type = {}
        affected_files = set()

        for d in all_drifts:
            by_severity[d.severity] = by_severity.get(d.severity, 0) + 1
            by_type[d.drift_type] = by_type.get(d.drift_type, 0) + 1
            affected_files.add(d.file_path)

        return {
            'total_unresolved': len(all_drifts),
            'by_severity': by_severity,
            'by_type': by_type,
            'affected_files': len(affected_files),
        }

    # ── Internal comparison ──

    def _compare_entity(self, old_e: Dict, new_e: Dict,
                        file_path: str) -> List[Dict[str, Any]]:
        """Compare two versions of the same entity."""
        drifts = []
        name = old_e['name']
        entity_type = new_e.get('type', old_e.get('type', 'unknown'))

        # Signature change
        old_sig = old_e.get('signature', '')
        new_sig = new_e.get('signature', '')
        if old_sig and new_sig and old_sig != new_sig:
            drifts.append({
                'file_path': file_path,
                'entity_name': name,
                'drift_type': 'signature_changed',
                'old_value': old_sig,
                'new_value': new_sig,
                'severity': _get_severity(entity_type, 'signature_changed'),
            })

        # Field comparison (for classes, models, DTOs, interfaces)
        old_fields = self._extract_field_map(old_e)
        new_fields = self._extract_field_map(new_e)

        if old_fields or new_fields:
            old_fnames = set(old_fields.keys())
            new_fnames = set(new_fields.keys())

            for removed in old_fnames - new_fnames:
                # Check for rename
                rename = self._find_field_rename(removed, old_fields[removed], new_fields, old_fnames)
                if rename:
                    drifts.append({
                        'file_path': file_path,
                        'entity_name': f"{name}.{removed}",
                        'drift_type': 'field_renamed',
                        'old_value': removed,
                        'new_value': rename,
                        'severity': _get_severity(entity_type, 'field_renamed'),
                    })
                else:
                    drifts.append({
                        'file_path': file_path,
                        'entity_name': f"{name}.{removed}",
                        'drift_type': 'field_removed',
                        'old_value': f"{removed}: {old_fields[removed].get('type', '?')}",
                        'new_value': None,
                        'severity': _get_severity(entity_type, 'field_removed'),
                    })

            for added in new_fnames - old_fnames:
                if not any(d['drift_type'] == 'field_renamed' and d['new_value'] == added for d in drifts):
                    drifts.append({
                        'file_path': file_path,
                        'entity_name': f"{name}.{added}",
                        'drift_type': 'field_added',
                        'old_value': None,
                        'new_value': f"{added}: {new_fields[added].get('type', '?')}",
                        'severity': _get_severity(entity_type, 'field_added'),
                    })

            for common in old_fnames & new_fnames:
                old_type = old_fields[common].get('type', '')
                new_type = new_fields[common].get('type', '')
                if old_type and new_type and old_type != new_type:
                    drifts.append({
                        'file_path': file_path,
                        'entity_name': f"{name}.{common}",
                        'drift_type': 'type_changed',
                        'old_value': old_type,
                        'new_value': new_type,
                        'severity': _get_severity(entity_type, 'type_changed'),
                    })

                old_opt = old_fields[common].get('optional', False)
                new_opt = new_fields[common].get('optional', False)
                if old_opt != new_opt:
                    drifts.append({
                        'file_path': file_path,
                        'entity_name': f"{name}.{common}",
                        'drift_type': 'nullability_changed',
                        'old_value': f"optional={old_opt}",
                        'new_value': f"optional={new_opt}",
                        'severity': _get_severity(entity_type, 'nullability_changed'),
                    })

        # Return type change (for functions/routes)
        old_meta = old_e.get('metadata', {}) or {}
        new_meta = new_e.get('metadata', {}) or {}
        old_ret = old_meta.get('returns', '')
        new_ret = new_meta.get('returns', '')
        if old_ret and new_ret and old_ret != new_ret:
            drifts.append({
                'file_path': file_path,
                'entity_name': name,
                'drift_type': 'return_type_changed',
                'old_value': old_ret,
                'new_value': new_ret,
                'severity': _get_severity(entity_type, 'return_type_changed'),
            })

        # Route method/path change
        old_route = old_meta.get('route', {}) or {}
        new_route = new_meta.get('route', {}) or {}
        if old_route and new_route:
            if old_route.get('method') and new_route.get('method') and old_route['method'] != new_route['method']:
                drifts.append({
                    'file_path': file_path,
                    'entity_name': name,
                    'drift_type': 'route_method_changed',
                    'old_value': old_route['method'],
                    'new_value': new_route['method'],
                    'severity': 'CRITICAL',
                })
            if old_route.get('path') and new_route.get('path') and old_route['path'] != new_route['path']:
                drifts.append({
                    'file_path': file_path,
                    'entity_name': name,
                    'drift_type': 'route_path_changed',
                    'old_value': old_route['path'],
                    'new_value': new_route['path'],
                    'severity': 'CRITICAL',
                })

        return drifts

    def _extract_field_map(self, entity: Dict) -> Dict[str, Dict]:
        """Extract a name→{type, optional, ...} map from entity metadata."""
        meta = entity.get('metadata', {}) or {}
        fields = meta.get('fields', [])
        if not isinstance(fields, list):
            return {}
        result = {}
        for f in fields:
            if isinstance(f, dict) and 'name' in f:
                result[f['name']] = f
        return result

    def _find_rename_candidate(self, old_entity: Dict, new_entities: Dict,
                                old_names: Set[str]) -> Optional[str]:
        """Check if a removed entity was renamed (similar structure in new set)."""
        old_fields = self._extract_field_map(old_entity)
        if not old_fields:
            return None

        best_match = None
        best_ratio = 0.0

        for name, new_e in new_entities.items():
            if name in old_names:
                continue  # Already exists
            new_fields = self._extract_field_map(new_e)
            if not new_fields:
                continue

            # Compare field name overlap
            old_fnames = set(old_fields.keys())
            new_fnames = set(new_fields.keys())
            if not old_fnames or not new_fnames:
                continue

            overlap = len(old_fnames & new_fnames) / max(len(old_fnames), len(new_fnames))
            name_sim = SequenceMatcher(None, old_entity['name'], name).ratio()
            score = overlap * 0.6 + name_sim * 0.4

            if score > best_ratio and score > 0.6:
                best_ratio = score
                best_match = name

        return best_match

    def _find_field_rename(self, removed_name: str, removed_field: Dict,
                           new_fields: Dict, old_names: Set[str]) -> Optional[str]:
        """Check if a removed field was just renamed."""
        removed_type = removed_field.get('type', '')
        if not removed_type:
            return None

        for name, fld in new_fields.items():
            if name in old_names:
                continue
            if fld.get('type', '') == removed_type:
                sim = SequenceMatcher(None, removed_name, name).ratio()
                if sim > 0.5:
                    return name

        return None
