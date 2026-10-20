"""Administrator account model."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.enums import Permission, Role, permissions_for


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    # Argon2 hash. The plaintext password is never stored or logged.
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(
        SAEnum(Role, native_enum=False, length=20), default=Role.ADMIN
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    @property
    def permissions(self) -> frozenset[Permission]:
        return permissions_for(self.role)

    def has_permission(self, perm: Permission) -> bool:
        return perm in self.permissions

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Admin id={self.id} email={self.email!r} role={self.role}>"
