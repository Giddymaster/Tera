"""Security primitives: password hashing, JWT tokens, enrollment secrets.

Nothing here logs or returns a plaintext secret except the generator functions,
whose output is shown to the admin exactly once and then only stored hashed.
"""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from app.core.config import get_settings

settings = get_settings()

# Argon2id with library defaults (a modern, memory-hard password hash).
_hasher = PasswordHasher()

TokenType = Literal["access", "refresh"]


class TokenError(Exception):
    """Raised when a token is missing, malformed, expired, or wrong-typed."""


# --------------------------------------------------------------------------- #
#  Passwords
# --------------------------------------------------------------------------- #
def hash_password(plaintext: str) -> str:
    return _hasher.hash(plaintext)


def verify_password(hashed: str, plaintext: str) -> bool:
    """Return True if the password matches. Never raises on a wrong password."""
    try:
        return _hasher.verify(hashed, plaintext)
    except (VerifyMismatchError, InvalidHashError):
        return False


def needs_rehash(hashed: str) -> bool:
    """True if the stored hash should be upgraded (params changed)."""
    try:
        return _hasher.check_needs_rehash(hashed)
    except InvalidHashError:
        return True


# --------------------------------------------------------------------------- #
#  JWT tokens
# --------------------------------------------------------------------------- #
def _create_token(subject: str, token_type: TokenType, expires: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires).timestamp()),
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(admin_id: int) -> str:
    return _create_token(
        str(admin_id), "access", timedelta(minutes=settings.access_token_minutes)
    )


def create_refresh_token(admin_id: int) -> str:
    return _create_token(
        str(admin_id), "refresh", timedelta(days=settings.refresh_token_days)
    )


def decode_token(token: str, expected_type: TokenType) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
    except jwt.ExpiredSignatureError as exc:
        raise TokenError("Token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise TokenError("Invalid token") from exc

    if payload.get("type") != expected_type:
        raise TokenError(f"Expected a {expected_type} token")
    if "sub" not in payload:
        raise TokenError("Token missing subject")
    return payload


# --------------------------------------------------------------------------- #
#  Device identifiers and enrollment secrets
# --------------------------------------------------------------------------- #
def generate_device_uid() -> str:
    """A public, opaque device identifier."""
    return "dev_" + secrets.token_urlsafe(16)


def generate_enrollment_secret() -> str:
    """A one-time device enrollment credential (plaintext, shown once)."""
    return secrets.token_urlsafe(32)


def hash_secret(plaintext: str) -> str:
    return _hasher.hash(plaintext)


def verify_secret(hashed: str, plaintext: str) -> bool:
    try:
        return _hasher.verify(hashed, plaintext)
    except (VerifyMismatchError, InvalidHashError):
        return False
