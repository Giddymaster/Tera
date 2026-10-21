"""Restore an encrypted database backup to a file.

Usage (backend/ dir, venv active):

    python scripts/restore.py --file backups/edm-backup-...db.enc --out restored.db

The restore writes to a new file by default (it does not overwrite the live DB).
Stop the server and swap files deliberately; see docs/backups.md.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.backup import BackupError, restore_backup  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Restore an encrypted backup.")
    parser.add_argument("--file", required=True, help="path to the .db.enc backup")
    parser.add_argument("--out", default="restored.db", help="output DB file path")
    args = parser.parse_args()
    try:
        out = restore_backup(args.file, args.out)
    except BackupError as exc:
        print(f"Restore failed: {exc}", file=sys.stderr)
        return 1
    print(f"Restored to: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
