"""Create an encrypted database backup and prune old ones.

Usage (backend/ dir, venv active):

    python scripts/backup.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.backup import BackupError, create_backup, prune_backups  # noqa: E402


def main() -> int:
    try:
        path = create_backup()
    except BackupError as exc:
        print(f"Backup failed: {exc}", file=sys.stderr)
        return 1
    removed = prune_backups()
    print(f"Backup written: {path.name}")
    if removed:
        print(f"Pruned {removed} old backup(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
