"""Encrypted database backups (SQLite) and restore.

Creates a consistent snapshot of the SQLite database (via ``VACUUM INTO``),
encrypts it at rest with the screenshot key, and writes it to the backup
directory. For PostgreSQL in production use ``pg_dump`` piped through encryption
(see docs/backups.md). The backup file is a secret and must be stored securely
(the backups directory is gitignored).
"""

from __future__ import annotations

import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import get_settings
from app.core.encryption import decrypt_bytes, encrypt_bytes

SQLITE_MAGIC = b"SQLite format 3\x00"


class BackupError(Exception):
    pass


def _sqlite_file() -> Path:
    url = get_settings().database_url
    if not url.startswith("sqlite"):
        raise BackupError(
            "Automated backup here supports SQLite only. For PostgreSQL use "
            "pg_dump with encryption; see docs/backups.md."
        )
    _, _, rest = url.partition(":///")
    return Path(rest)


def create_backup(dest_dir: str | Path | None = None) -> Path:
    settings = get_settings()
    dest = Path(dest_dir or settings.backup_dir)
    dest.mkdir(parents=True, exist_ok=True)
    src = _sqlite_file()

    with tempfile.TemporaryDirectory() as tmp:
        snapshot = Path(tmp) / "snapshot.db"
        con = sqlite3.connect(str(src))
        try:
            # Consistent, online snapshot without blocking writers for long.
            con.execute("VACUUM INTO ?", (str(snapshot),))
        finally:
            con.close()
        data = snapshot.read_bytes()

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = dest / f"edm-backup-{ts}.db.enc"
    out.write_bytes(encrypt_bytes(data))
    return out


def restore_backup(enc_path: str | Path, dest_path: str | Path) -> Path:
    data = decrypt_bytes(Path(enc_path).read_bytes())
    if not data.startswith(SQLITE_MAGIC):
        raise BackupError("Decrypted backup is not a valid SQLite database.")
    out = Path(dest_path)
    out.write_bytes(data)
    return out


def prune_backups(dest_dir: str | Path | None = None, keep: int | None = None) -> int:
    settings = get_settings()
    dest = Path(dest_dir or settings.backup_dir)
    keep = keep if keep is not None else settings.backup_keep
    files = sorted(dest.glob("edm-backup-*.db.enc"))
    to_remove = files[:-keep] if len(files) > keep else []
    for f in to_remove:
        f.unlink()
    return len(to_remove)
