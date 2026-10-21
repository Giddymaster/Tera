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
- **Agent API** (`app/api/agent.py`) — `POST /agent/enroll` (single-use secret →
  device token), `POST /agent/heartbeat` (check-in updating last-seen plus
  reported agent/OS version and health: disk, battery, power), and
  `POST /agent/usage` (foreground app names + durations, accumulated per app per
  day). Device tokens are a distinct token type and are rejected on admin
  endpoints; revoked devices are refused.
- **Usage view** — `GET /devices/{uid}/usage` (admins with `view_reports`)
  returns per-app totals over a window of days.
- **Screenshots** (`app/api/screenshots.py`, `app/api/agent.py`) — per-device
  policy (`manage_security_policy` to change), capture requests, `GET /agent/
  directives` + `POST /agent/screenshot` for the device, and list/view/delete for
  admins with `view_screenshots`. Images are encrypted at rest and retained per
  policy.
- **Remote support** (`app/api/sessions.py`) — start/end sessions
  (`initiate_live_session`), list sessions, and view a session's snapshots
  (`view_screenshots`).
- **Android** (`app/api/android.py`, `app/core/android.py`) — Android Management
  API integration scaffold: `GET /android/status` (capability matrix, always
  available) plus device list, enrollment token, and commands, gated on
  configuration (see docs/android-feasibility.md). The live path is untested
  without a Google project and device.
- **Apple** (`app/api/apple.py`, `app/core/apple.py`) — `GET /apple/status` with
  the Apple MDM capability matrix and enrollment models. A live MDM server
  (APNs cert + ABM + device) is required for actual management and is not
  implemented here (see docs/apple-mdm-feasibility.md).
- **Location** (`app/api/location.py`) — opt-in per-device location: policy,
  on-demand request, `POST /agent/location` (device), and history with a freshness
  indicator for admins with `view_reports`. Coordinates are stored only for a real
  fix; unavailable/permission-restricted results are never invented.
- **Alerts & reports** (`app/api/reports.py`) — `GET /alerts` (derived device
  alerts) and `GET /reports/summary` (fleet counts).
- **Audit API** (`app/api/audit.py`) — `GET /audit` for admins with
  `view_reports`, newest first, paginated.
- **Migrations** (`migrations/`) — Alembic; initial schema plus a device-health
  column migration.
- **Tests** (`../tests/backend/`) — 87 tests covering auth, authorization,
  device enrollment/heartbeat, token separation, revocation, device health,
  app-usage, screenshots, remote sessions, retention, location, derived alerts,
  fleet summary, Android/Apple status, security headers, full-device-data
  deletion (cascade + blobs), backup/restore, validation, rate limiting, and
  audit logging.
- **Ops scripts** (`scripts/`) — `backup.py` / `restore.py` (encrypted DB
  backups), `retention_cleanup.py` (all data-retention cleanups), plus
  `create_admin.py`, `seed_demo.py`, `simulate_agent.py`,
  `cleanup_screenshots.py`. See docs/backups.md.

## Try the full agent flow

With the server running and a demo admin created, simulate a device enrolling and
checking in (it will appear "Online" in the dashboard):

```bash
python scripts/simulate_agent.py --email admin@demo.local --password <password>
```

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
- Device tokens are stateless; revocation is via device status, not a per-token
  blocklist.
- Heartbeat is exercised by a simulated agent; the real Windows agent is
  Milestone 5.
