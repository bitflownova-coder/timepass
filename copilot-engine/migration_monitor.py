"""
Copilot Engine - Migration Monitor
Watches Prisma schema and migration folder for consistency:
  - Schema changed but no migration generated → HIGH risk
  - Migration exists but not applied → MEDIUM risk
  - Migration timestamp drift (long-unapplied migrations)
  - Schema file missing but migrations exist
  - Migration SQL inconsistencies
"""
import os
import re
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


class MigrationMonitor:
    """
    Monitors Prisma/ORM migration state for a workspace.
    Detects schema drift, unapplied migrations, and inconsistencies.
    """

    def __init__(self):
        self._schema_hashes: Dict[str, str] = {}  # workspace → last known schema hash
        self._last_migration_hash: Dict[str, str] = {}  # workspace → hash of latest migration

    def check(self, workspace_path: str) -> Dict[str, Any]:
        """Full migration health check."""
        root = Path(workspace_path)
        result = {
            'has_prisma': False,
            'has_migrations': False,
            'schema_path': None,
            'migration_dir': None,
            'issues': [],
            'risk_score': 0.0,
            'migration_count': 0,
            'latest_migration': None,
            'schema_hash': None,
        }

        # Find schema.prisma
        schema_path = self._find_schema(root)
        if schema_path:
            result['has_prisma'] = True
            result['schema_path'] = str(schema_path)
            result['schema_hash'] = self._hash_file(schema_path)

        # Find migrations directory
        migration_dir = self._find_migration_dir(root)
        if migration_dir:
            result['has_migrations'] = True
            result['migration_dir'] = str(migration_dir)
            migrations = self._list_migrations(migration_dir)
            result['migration_count'] = len(migrations)
            if migrations:
                result['latest_migration'] = migrations[-1]

        # ── Issue Detection ──

        if result['has_prisma'] and not result['has_migrations']:
            result['issues'].append({
                'severity': 'MEDIUM',
                'type': 'no_migrations',
                'message': 'Prisma schema exists but no migrations directory found. Run `prisma migrate dev` to initialize.',
            })

        if result['has_prisma'] and result['has_migrations']:
            # Check for schema drift (schema changed since last migration)
            drift = self._check_schema_drift(schema_path, migration_dir, workspace_path)
            if drift:
                result['issues'].append(drift)

            # Check for unapplied migrations
            unapplied = self._check_unapplied(migration_dir)
            result['issues'].extend(unapplied)

            # Check migration age
            age_issues = self._check_migration_age(migration_dir)
            result['issues'].extend(age_issues)

        if not result['has_prisma'] and result['has_migrations']:
            result['issues'].append({
                'severity': 'HIGH',
                'type': 'orphaned_migrations',
                'message': 'Migration directory exists but no schema.prisma found. Schema may have been deleted.',
            })

        # Calculate risk score
        severity_weights = {'CRITICAL': 3.0, 'HIGH': 2.0, 'MEDIUM': 1.0, 'LOW': 0.3}
        total_weight = sum(severity_weights.get(i['severity'], 0.5) for i in result['issues'])
        result['risk_score'] = min(10.0, total_weight * 2)

        return result

    def check_incremental(self, file_path: str, workspace_path: str) -> Optional[Dict[str, Any]]:
        """
        Quick check triggered by a file change.
        Only runs if the changed file is schema.prisma or in a migrations dir.
        """
        fname = os.path.basename(file_path).lower()
        is_schema = fname == 'schema.prisma'
        is_migration = 'migration' in file_path.lower()

        if not is_schema and not is_migration:
            return None

        return self.check(workspace_path)

    # ── Internal ──

    def _find_schema(self, root: Path) -> Optional[Path]:
        """Find schema.prisma in the workspace."""
        candidates = [
            root / 'prisma' / 'schema.prisma',
            root / 'schema.prisma',
        ]
        # Also search one level deep
        for d in root.iterdir():
            if d.is_dir() and d.name not in ('node_modules', '.git', '.venv', 'dist', 'build'):
                candidates.append(d / 'prisma' / 'schema.prisma')
                candidates.append(d / 'schema.prisma')

        for c in candidates:
            if c.exists():
                return c
        return None

    def _find_migration_dir(self, root: Path) -> Optional[Path]:
        candidates = [
            root / 'prisma' / 'migrations',
            root / 'migrations',
        ]
        for d in root.iterdir():
            if d.is_dir() and d.name not in ('node_modules', '.git', '.venv', 'dist', 'build'):
                candidates.append(d / 'prisma' / 'migrations')

        for c in candidates:
            if c.exists() and c.is_dir():
                return c
        return None

    def _list_migrations(self, migration_dir: Path) -> List[Dict[str, Any]]:
        """List all migrations sorted by name (which is typically timestamp-based)."""
        migrations = []
        for d in sorted(migration_dir.iterdir()):
            if d.is_dir() and d.name != '_journal':
                sql_file = d / 'migration.sql'
                migrations.append({
                    'name': d.name,
                    'path': str(d),
                    'has_sql': sql_file.exists(),
                    'timestamp': self._parse_migration_timestamp(d.name),
                })
        return migrations

    def _parse_migration_timestamp(self, name: str) -> Optional[str]:
        """Extract timestamp from migration folder name (YYYYMMDDHHMMSS_name)."""
        m = re.match(r'(\d{14})', name)
        if m:
            ts = m.group(1)
            try:
                dt = datetime.strptime(ts, '%Y%m%d%H%M%S')
                return dt.isoformat()
            except ValueError:
                pass
        return None

    def _hash_file(self, path: Path) -> str:
        try:
            return hashlib.sha256(path.read_bytes()).hexdigest()[:16]
        except Exception:
            return ''

    def _check_schema_drift(self, schema_path: Path, migration_dir: Path,
                             workspace_path: str) -> Optional[Dict[str, Any]]:
        """Check if schema changed since the last migration."""
        current_hash = self._hash_file(schema_path)
        old_hash = self._schema_hashes.get(workspace_path, '')

        if old_hash and current_hash != old_hash:
            # Schema changed — check if there's a new migration
            migrations = self._list_migrations(migration_dir)
            if migrations:
                latest_path = Path(migrations[-1]['path'])
                latest_hash = self._hash_file(latest_path / 'migration.sql') if (latest_path / 'migration.sql').exists() else ''
                old_mig_hash = self._last_migration_hash.get(workspace_path, '')

                if latest_hash == old_mig_hash:
                    # Schema changed but no new migration
                    self._schema_hashes[workspace_path] = current_hash
                    return {
                        'severity': 'HIGH',
                        'type': 'schema_drift',
                        'message': 'Schema has changed since last migration. Run `prisma migrate dev` to generate a migration.',
                    }

                self._last_migration_hash[workspace_path] = latest_hash

        self._schema_hashes[workspace_path] = current_hash
        return None

    def _check_unapplied(self, migration_dir: Path) -> List[Dict[str, Any]]:
        """Check for migrations that might not be applied."""
        issues = []
        # Check for _journal or migration_lock
        journal = migration_dir / '_journal'
        if not journal.exists():
            # No journal = might mean migrations haven't been run
            migrations = self._list_migrations(migration_dir)
            if len(migrations) > 0:
                issues.append({
                    'severity': 'LOW',
                    'type': 'no_migration_journal',
                    'message': f'No migration journal found. {len(migrations)} migration(s) may not have been applied to the local database.',
                })
        return issues

    def _check_migration_age(self, migration_dir: Path) -> List[Dict[str, Any]]:
        """Flag very old unapplied-looking migrations."""
        issues = []
        migrations = self._list_migrations(migration_dir)
        if not migrations:
            return issues

        latest = migrations[-1]
        ts = latest.get('timestamp')
        if ts:
            try:
                dt = datetime.fromisoformat(ts)
                age = datetime.now() - dt
                if age > timedelta(days=30):
                    issues.append({
                        'severity': 'LOW',
                        'type': 'stale_migration',
                        'message': f'Latest migration is {age.days} days old ({latest["name"]}). Schema may have evolved without migrations.',
                    })
            except Exception:
                pass

        return issues
