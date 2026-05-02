import argparse
import os
import time
import zipfile
from pathlib import Path

from dotenv import load_dotenv


def _iter_files(root: Path):
    for path in root.rglob('*'):
        if path.is_file():
            yield path


def _add_path(zf: zipfile.ZipFile, path: Path, base: Path):
    for file_path in _iter_files(path):
        rel = file_path.relative_to(base)
        zf.write(file_path, rel.as_posix())


def _cleanup_old(backups_dir: Path, retention_days: int):
    if retention_days <= 0:
        return
    cutoff = time.time() - (retention_days * 86400)
    for item in backups_dir.glob('backup_*.zip'):
        try:
            if item.stat().st_mtime < cutoff:
                item.unlink()
        except Exception:
            continue


def main() -> int:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Create a backup archive")
    parser.add_argument('--out', help='Backup directory (overrides BACKUP_DIR)')
    args = parser.parse_args()

    backup_dir = Path(args.out or os.getenv('BACKUP_DIR', 'backups'))
    retention_days = int(os.getenv('BACKUP_RETENTION_DAYS', '7'))
    include_logs = os.getenv('BACKUP_INCLUDE_LOGS', 'false').lower() == 'true'

    backup_dir.mkdir(parents=True, exist_ok=True)

    ts = time.strftime('%Y%m%d_%H%M%S')
    backup_path = backup_dir / f'backup_{ts}.zip'

    project_root = Path.cwd()
    targets = []

    db_path = project_root / 'instance' / 'app.db'
    if db_path.exists():
        targets.append(db_path)

    uploads_path = project_root / 'data' / 'uploads'
    if uploads_path.exists():
        targets.append(uploads_path)

    if include_logs:
        logs_path = project_root / 'logs'
        if logs_path.exists():
            targets.append(logs_path)

    if not targets:
        print('Nothing to back up.')
        return 1

    with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for target in targets:
            if target.is_file():
                zf.write(target, target.relative_to(project_root).as_posix())
            else:
                _add_path(zf, target, project_root)

    _cleanup_old(backup_dir, retention_days)
    print(f'Backup created: {backup_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
