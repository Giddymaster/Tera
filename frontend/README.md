# frontend

React + Vite + TypeScript admin dashboard for the Employee Device Manager. It
talks to the backend API (Milestone 2) and, in Milestone 3, shows an admin login
and a device overview populated with simulated devices.

## What exists after Milestone 3

- **Login** (`src/pages/LoginPage.tsx`) — authenticates against the backend; the
  session is restored on reload and refreshed automatically.
- **Protected routing** (`src/auth/`) — only signed-in admins reach the dashboard.
- **Device overview** (`src/pages/DashboardPage.tsx`) — summary cards plus a
  searchable device table.
- **Device detail** (`src/pages/DeviceDetailPage.tsx`) — enrollment info and
  status, with placeholders for data that arrives in later milestones.
- **Honest status** (`src/lib/deviceStatus.ts`) — a device is "online" only if
  its last check-in is within 5 minutes.

## Prerequisites

- The backend must be running (see `../backend/README.md`).
- An admin account must exist, and some devices should be seeded:

```bash
cd ../backend
.\.venv\Scripts\python.exe scripts\create_admin.py --email you@example.com --role owner
.\.venv\Scripts\python.exe scripts\seed_demo.py --yes
```

## Run the dashboard

```bash
npm install
npm run dev
```

Open the URL Vite prints (default http://localhost:5173) and sign in.

## Build and type-check

```bash
npm run build     # runs tsc then produces a production build in dist/
```

## Configuration

The API base URL is read from `VITE_API_BASE_URL` (default
`http://localhost:8000`). To point at a different backend, create
`frontend/.env.local`:

```
VITE_API_BASE_URL=http://localhost:8000
```

## Notes and limitations

- Tokens are stored in `localStorage` for now. This is simple but readable by any
  script on the page; a future hardening step (security milestone) is to move to
  httpOnly, SameSite cookies issued by the backend.
- The dashboard refreshes on page load and via the **Refresh** button. Live push
  updates over WebSockets arrive in Milestone 4.
- The devices shown are **simulated** seed data until the real agent exists.
