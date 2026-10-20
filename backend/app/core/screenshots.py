"""Encrypted screenshot storage on disk, plus retention cleanup.

Image bytes never touch the database and are never written to disk in the clear:
they are encrypted with the screenshot key before being written, and decrypted
only when an authorized admin views them.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.encryption import decrypt_bytes, encrypt_bytes
from app.models.monitoring import Screenshot

settings = get_settings()
_BASE = Path(settings.screenshot_dir)


def _dir_for(device_uid: str) -> Path:
    d = _BASE / device_uid
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_encrypted(device_uid: str, data: bytes) -> str:
    """Encrypt and store image bytes; return the relative storage path."""
    name = f"{uuid.uuid4().hex}.enc"
    (_dir_for(device_uid) / name).write_bytes(encrypt_bytes(data))
    return f"{device_uid}/{name}"


def load_decrypted(storage_path: str) -> bytes:
    return decrypt_bytes((_BASE / storage_path).read_bytes())


def delete_blob(storage_path: str) -> None:
    try:
        (_BASE / storage_path).unlink()
    except FileNotFoundError:
        pass


async def delete_expired(session: AsyncSession) -> int:
    """Delete screenshots whose retention period has passed. Returns the count."""
    now = datetime.now(timezone.utc)
    rows = (
        await session.execute(
            select(Screenshot).where(Screenshot.retention_until < now)
        )
    ).scalars().all()
    for row in rows:
        delete_blob(row.storage_path)
    if rows:
        await session.execute(
            delete(Screenshot).where(Screenshot.id.in_([r.id for r in rows]))
        )
        await session.commit()
    return len(rows)
