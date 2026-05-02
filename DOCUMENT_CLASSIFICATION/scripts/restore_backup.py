import argparse
import os
import zipfile
from pathlib import Path

from dotenv import load_dotenv


def main() -> int:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Restore a backup archive")
    parser.add_argument('file', help='Path to backup zip')
    parser.add_argument('--overwrite', action='store_true', help='Overwrite existing files')
    args = parser.parse_args()

    backup_path = Path(args.file)
    if not backup_path.exists():
        print(f'Backup not found: {backup_path}')
        return 1

    project_root = Path.cwd()

    with zipfile.ZipFile(backup_path, 'r') as zf:
        for member in zf.infolist():
            dest = project_root / member.filename
            if dest.exists() and not args.overwrite:
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            zf.extract(member, project_root)

    print('Restore complete.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
