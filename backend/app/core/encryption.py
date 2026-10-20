"""Symmetric encryption for screenshots at rest (Fernet / AES-128-CBC + HMAC)."""

from __future__ import annotations

from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings


@lru_cache
def _fernet() -> Fernet:
    key = get_settings().screenshot_key
    try:
        return Fernet(key.encode() if isinstance(key, str) else key)
    except (ValueError, TypeError) as exc:  # pragma: no cover - config error
        raise RuntimeError(
            "SCREENSHOT_KEY is not a valid Fernet key (urlsafe base64, 32 bytes)."
        ) from exc


def encrypt_bytes(data: bytes) -> bytes:
    return _fernet().encrypt(data)


def decrypt_bytes(token: bytes) -> bytes:
    try:
        return _fernet().decrypt(token)
    except InvalidToken as exc:
        raise ValueError("Could not decrypt screenshot (wrong key or corrupt).") from exc
