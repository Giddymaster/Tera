# Employee Device Manager

A self-hosted, open-source platform for a small business to manage and monitor
its **own company-owned devices** (1–10): Windows laptops, Android phones, and
iPhones. It provides a central admin dashboard, device enrollment, health and
activity reporting, policy-controlled screenshots, and authorized remote support.

This project is built incrementally in milestones. **It is currently at
Milestone 8: Android management.** The backend, a React dashboard, and a real
Windows agent are tested on Windows 11 (device health, foreground app usage,
policy-controlled encrypted screenshots, and authorized live support). Milestone 8
adds a researched Android feasibility assessment and an Android Management API
integration scaffold with an honest capability matrix; the live Android path needs
a Google Cloud project and a device and is documented, not yet tested. There is no
keylogging, clipboard, window-title, screenshot, or app-usage capture on Android.
See [docs/android-feasibility.md](docs/android-feasibility.md) and
[docs/data-collection.md](docs/data-collection.md).

---

## Important: lawful and transparent use

This software is intended **only** for devices that your organization owns and is
authorized to manage, with monitoring that is disclosed to the people using those
devices. By design it:

- shows a visible monitoring notice on managed devices;
- requires authenticated, authorized administrators for every sensitive action;
- records audit logs of who did what;
- excludes passwords, authentication codes, and private form contents from collection;
- does **not** implement hidden installation, process hiding, keylogging, covert
  microphone/screen capture, or security-software evasion.

Monitoring employees is regulated and the rules differ by country, state, and
employment contract. Confirm your legal obligations (notice, consent, data
protection) before deploying this to real devices. This README is not legal advice.

---

## Technology stack

| Layer            | Technology                                              |
| ---------------- | ------------------------------------------------------- |
| Frontend         | React + Vite + TypeScript                               |
| Backend          | Python + FastAPI (REST + WebSockets)                    |
| Database         | PostgreSQL (production) / SQLite (local dev)            |
| Windows agent    | Python prototype                                        |
| Mobile           | Android Enterprise + Apple MDM (feasibility first)      |
| Deployment       | Docker + Docker Compose, HTTPS, free-tier/self-hosted   |

## Project structure

```
TERA/
├── frontend/           React + Vite + TypeScript dashboard
├── backend/            FastAPI REST API, WebSockets, DB models
│   ├── app/
│   │   ├── api/        Route handlers
│   │   ├── core/       Config, security, settings
│   │   ├── models/     Database models
│   │   └── schemas/    Request/response validation
│   └── migrations/     Database migrations
├── windows-agent/      Windows device agent (Python prototype)
├── mobile-management/  Android (Enterprise) and iOS (MDM) management
│   ├── android/
│   └── ios/
├── deployment/         Docker, compose files, hosting config
├── docs/               Architecture, compatibility table, runbooks
├── tests/              Automated tests
├── .gitignore
├── .env.example        Template for environment variables
└── README.md
```

## Prerequisites (verified on this machine)

| Tool   | Required | Detected    |
| ------ | -------- | ----------- |
| Node   | 20+      | v25.2.1     |
| npm    | 10+      | 11.19.0     |
| Python | 3.11+    | 3.14.2      |
| pip    | —        | 26.0        |
| Git    | 2.x      | 2.52.0      |
| Docker | optional | 29.8 (daemon not running yet) |

> **Note on very new runtimes:** Node 25 and Python 3.14 are newer than most
> libraries' tested versions. If a dependency fails to install in a later
> milestone, the fix is usually to pin a compatible version, not to change your
> approach. We will handle that when we add dependencies.

## Milestone 1 setup

Milestone 1 only creates the repository and folder structure. There is nothing to
run yet — the backend and frontend apps are added in Milestone 2 and 3.

**1. Initialize version control** (run from the project root):

```bash
git init
git add .
git commit -m "Milestone 1: project structure and scaffolding"
```

**2. Create your local environment file** (never commit it):

```bash
Copy-Item .env.example .env
```

Then open `.env` and fill in values as later milestones require them.

**3. Verify the structure:**

```bash
Get-ChildItem -Recurse -Depth 1 -Directory
```

You should see the folders listed under *Project structure* above.

## Roadmap (milestones)

1. ✅ Project structure and scaffolding
2. ✅ Backend, database, admin authentication, device APIs
3. ✅ React dashboard with simulated devices
4. ✅ Device registration, heartbeat, status, audit logs
5. ✅ Windows agent: device health + foreground app usage
6. ✅ Managed startup, secure updates, agent recovery
7. ✅ Policy-controlled screenshots + authorized live remote support
8. **Android management feasibility + implementation** ← you are here
9. Apple MDM feasibility + implementation
10. Location features, alerts, reporting
11. Security review, backups, retention, automated tests
12. Cloud deployment and gradual rollout

See [docs/compatibility.md](docs/compatibility.md) for the per-platform feature
status table. A feature is only marked supported after it is implemented and
tested on the relevant operating system.

## License

To be decided before the first public release. Until a `LICENSE` file is added,
treat this as all-rights-reserved and do not redistribute.
