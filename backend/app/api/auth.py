"""Administrator authentication routes."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select

from app.api.deps import CurrentAdmin, SessionDep, client_ip
from app.core.audit import record_action
from app.core.config import get_settings
from app.core.rate_limit import SlidingWindowLimiter
from app.core.security import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    needs_rehash,
    verify_password,
)
from app.models.admin import Admin
from app.schemas.auth import AdminOut, LoginRequest, RefreshRequest, TokenResponse

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["auth"])

# Per-IP login limiter. Exposed at module level so tests can reset it.
login_limiter = SlidingWindowLimiter(
    max_attempts=settings.login_max_attempts,
    window_seconds=settings.login_window_seconds,
)


def _admin_out(admin: Admin) -> AdminOut:
    out = AdminOut.model_validate(admin)
    out.permissions = sorted(p.value for p in admin.permissions)
    return out


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, request: Request, session: SessionDep):
    ip = client_ip(request)
    if not login_limiter.is_allowed(ip):
        retry = login_limiter.retry_after(ip)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please wait and try again.",
            headers={"Retry-After": str(retry)},
        )

    result = await session.execute(
        select(Admin).where(Admin.email == payload.email.lower().strip())
    )
    admin = result.scalar_one_or_none()

    # One identical response for "unknown email" and "wrong password" so the
    # endpoint cannot be used to discover which emails exist.
    invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password",
    )

    if admin is None or not admin.is_active:
        await record_action(
            session, action="admin.login_failed", detail=f"email={payload.email}",
            ip_address=ip,
        )
        raise invalid

    if not verify_password(admin.hashed_password, payload.password):
        await record_action(
            session, action="admin.login_failed", actor=admin, ip_address=ip,
        )
        raise invalid

    # Successful login: transparently upgrade the hash if parameters changed.
    if needs_rehash(admin.hashed_password):
        admin.hashed_password = hash_password(payload.password)
    admin.last_login_at = datetime.now(timezone.utc)
    await record_action(
        session, action="admin.login", actor=admin, ip_address=ip, commit=False
    )
    await session.commit()
    # A clean login clears the IP's recent-attempt count.
    login_limiter.reset(ip)

    return TokenResponse(
        access_token=create_access_token(admin.id),
        refresh_token=create_refresh_token(admin.id),
        expires_in=settings.access_token_minutes * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, session: SessionDep):
    try:
        claims = decode_token(payload.refresh_token, expected_type="refresh")
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from None

    admin = await session.get(Admin, int(claims["sub"]))
    if admin is None or not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    # Rotate both tokens on refresh.
    return TokenResponse(
        access_token=create_access_token(admin.id),
        refresh_token=create_refresh_token(admin.id),
        expires_in=settings.access_token_minutes * 60,
    )


@router.get("/me", response_model=AdminOut)
async def me(admin: CurrentAdmin):
    return _admin_out(admin)
