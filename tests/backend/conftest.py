"""Pytest fixtures for backend tests.

A fresh, isolated SQLite test database is created in a temp directory and the
schema is rebuilt before every test, so tests never touch your dev.db and never
affect each other. Admins are seeded through the ORM (so enum storage matches
exactly what the app reads back).
"""

from __future__ import annotations

import base64
import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

# ---- Configure the environment BEFORE importing anything from `app`. ----
_TMP_DIR = tempfile.mkdtemp(prefix="edm-tests-")
_DB_PATH = Path(_TMP_DIR) / "test.db"
os.environ["APP_ENV"] = "development"
os.environ["JWT_SECRET"] = "test-secret-fixed-value-for-deterministic-tokens"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_DB_PATH.as_posix()}"
# Fixed Fernet key (urlsafe base64 of 32 bytes) and an isolated screenshot dir.
os.environ["SCREENSHOT_KEY"] = base64.urlsafe_b64encode(b"0" * 32).decode()
os.environ["SCREENSHOT_DIR"] = str(Path(_TMP_DIR) / "screenshots")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

from app.api.agent import enroll_limiter  # noqa: E402
from app.api.auth import login_limiter  # noqa: E402
from app.core.database import Base  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Admin  # noqa: E402
from app.models.enums import Role  # noqa: E402

# A synchronous engine to the same file, used only for test setup/seeding.
_sync_engine = create_engine(f"sqlite:///{_DB_PATH.as_posix()}")
_SyncSession = sessionmaker(bind=_sync_engine, class_=Session)


@pytest.fixture(autouse=True)
def _fresh_db() -> Iterator[None]:
    """Rebuild the schema and clear rate-limit state before each test."""
    Base.metadata.drop_all(_sync_engine)
    Base.metadata.create_all(_sync_engine)
    login_limiter.reset()
    enroll_limiter.reset()
    yield


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sync_session() -> Iterator[Session]:
    """A synchronous DB session for assertions (e.g. reading audit rows)."""
    with _SyncSession() as s:
        yield s


@pytest.fixture
def make_admin():
    """Factory: create an admin and return (admin_id, email, password)."""

    def _make(
        email: str = "owner@example.com",
        password: str = "correct horse battery",
        role: Role = Role.OWNER,
    ) -> tuple[int, str, str]:
        with _SyncSession() as s:
            admin = Admin(
                email=email.lower().strip(),
                hashed_password=hash_password(password),
                role=role,
            )
            s.add(admin)
            s.commit()
            return admin.id, email, password

    return _make


@pytest.fixture
def auth_headers(client: TestClient, make_admin):
    """Factory: create an admin with a role and return Bearer auth headers."""

    def _headers(
        email: str = "owner@example.com",
        password: str = "correct horse battery",
        role: Role = Role.OWNER,
    ) -> dict[str, str]:
        make_admin(email=email, password=password, role=role)
        resp = client.post("/auth/login", json={"email": email, "password": password})
        assert resp.status_code == 200, resp.text
        token = resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _headers
