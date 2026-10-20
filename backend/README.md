# backend

FastAPI backend for the Employee Device Manager: admin authentication, device
management APIs, audit logging, and a database layer (SQLite for local dev,
PostgreSQL for production).

## What exists after Milestone 2

- **Config** (`app/core/config.py`) — loaded from environment / `.env`; refuses
  to start in production without a real `JWT_SECRET`.
- **Database** (`app/core/database.py`) — async SQLAlchemy; SQLite locally.
- **Models** (`app/models/`) — `Admin`, `Device`, `AuditLog`.
- **Security** (`app/core/security.py`) — Argon2 password hashing, JWT access &
  refresh tokens, device enrollment secrets.
- **Auth API** (`app/api/auth.py`) — `POST /auth/login`, `POST /auth/refresh`,
  `GET /auth/me`, with per-IP login rate limiting.
- **Device API** (`app/api/devices.py`) — create / list / get / revoke / delete,
  each guarded by a role-based permission and written to the audit log.
- **Migrations** (`migrations/`) — Alembic, initial schema generated.
- **Tests** (`../tests/backend/`) — 27 tests covering auth, authorization,
  enrollment, validation, rate limiting, and audit logging.

## Setup (Windows PowerShell)

From the `backend/` directory:

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> If activation is blocked by execution policy, run PowerShell once as:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, or just call the venv
> Python directly: `.\.venv\Scripts\python.exe`.

## Create the first admin

No default password ships with the app. Create an owner account:

```bash
python scripts/create_admin.py --email you@example.com --role owner
```

You will be prompted for a password (hidden input). Roles: `owner`, `admin`,
`viewer`.

## Run the server

```bash
uvicorn app.main:app --reload
```

Then open:

- API docs (Swagger UI): http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

## Run the tests

```bash
python -m pytest
```

Tests use their own temporary SQLite database and never touch `dev.db`.

## Database migrations

Local development auto-creates tables on startup. For production (PostgreSQL),
use Alembic:

```bash
alembic upgrade head                      # apply migrations
alembic revision --autogenerate -m "..."  # create a new migration after model changes
```

PostgreSQL note: migrations run on a **sync** driver. Install `psycopg` and set
`DATABASE_URL=postgresql+asyncpg://...`; the migration env converts it to the
sync equivalent automatically.

## Roles and permissions

| Permission               | owner | admin | viewer |
| ------------------------ | :---: | :---: | :----: |
| view_devices             |  ✅   |  ✅   |   ✅   |
| view_reports             |  ✅   |  ✅   |   ✅   |
| manage_devices           |  ✅   |  ✅   |        |
| view_screenshots         |  ✅   |  ✅   |        |
| initiate_live_session    |  ✅   |  ✅   |        |
| manage_security_policy   |  ✅   |       |        |
| manage_admins            |  ✅   |       |        |

Endpoints check a **permission**, never a role directly, so the mapping above can
change without touching endpoint code.

## Known limitations (to revisit in later milestones)

- Refresh tokens are stateless (no server-side revocation list yet).
- Rate limiting is in-process memory only; a multi-process deployment needs a
  shared store (e.g. Redis).
- No MFA yet (planned where practical).
- Agent-facing enrollment/heartbeat endpoints arrive in Milestone 4.
