# Deployment and hosting

This guide compares hosting options (with their real limits), recommends an
approach for a small business managing sensitive company-device data, gives the
production stack, and lays out a safe staged rollout. Facts verified 2026-10-21;
free tiers change often, so re-check each provider's pricing page before relying
on it.

## Honest bottom line

There is **no fully-free cloud option that is also reliable and suitable for
sensitive company data** for this system, because:

- Free backend tiers (e.g. Render free) **sleep after ~15 min idle** and have
  **ephemeral storage**. A sleeping backend misses agent check-ins (devices look
  falsely offline), and ephemeral storage would lose encrypted screenshots and a
  SQLite database on restart.
- Free managed Postgres is small and idles/pauses (Neon ~0.5 GB auto-suspend;
  Supabase ~500 MB, pauses after 7 days idle).

**Recommended:** self-host the Docker stack on a **small VPS (~$4–6/month)** or an
**on-prem mini-PC** (no hosting fee; data stays in-house — often best for
sensitive data). Both keep PostgreSQL private, keep encrypted screenshots on a
persistent volume, and give reliable always-on check-ins. **Production hosting is
not free indefinitely** — budget a few dollars a month, or run on-prem.

## Option comparison

| Need | Free option | Genuine free tier? | Card? | Idle behavior | Sensitive-data fit | If it grows |
| --- | --- | --- | --- | --- | --- | --- |
| Frontend (static) | Cloudflare Pages | Yes, unmetered bandwidth | No | No sleep | OK (static only) | Stays generous |
| Frontend (static) | Netlify / Vercel | Vercel Hobby is **non-commercial**; Netlify credit-based | Varies | No sleep | Vercel: not for business | Paid plans |
| Backend API | Render free web service | Yes, 750 hrs/mo | No | **Sleeps ~15 min idle**, ephemeral disk | **Poor** (sleep + ephemeral) | ~$7/mo to stop sleeping |
| Backend API | Fly.io / small VPS | VPS ~$4–6/mo (not free) | Yes | Always on | **Good** | Scales with VPS size |
| PostgreSQL | Neon free | 0.5 GB, auto-suspend | No | Suspends compute (~5 min) | OK for small; keep private | $/GB beyond |
| PostgreSQL | Supabase free | 500 MB, 2 projects | No | **Pauses after 7 days idle** | OK; unpause needed | Paid plan |
| Screenshot storage | Cloudflare R2 / Backblaze B2 | ~10 GB free, low/no egress | Card (R2) | n/a | OK **if bucket is private** | $/GB beyond |
| TLS certificates | Let's Encrypt (via Caddy) | Yes | No | n/a | Good | Free |
| Uptime monitoring | UptimeRobot free + `/health` | Yes | No | n/a | Good | Paid tiers |
| Backups | This project's encrypted backup + object storage | Yes | n/a | n/a | Good | $/GB |

### Hard rules (from the project requirements)

- **Never expose PostgreSQL to the public internet.** In the stack below it has no
  published port and is reachable only on the internal Docker network.
- **Never use public, unauthenticated storage** for screenshots or backups. If you
  move screenshots to object storage, use a **private** bucket with scoped keys.

## Production stack (self-hosted, recommended)

Everything is in `deployment/`:

- `Dockerfile.backend` — FastAPI on `python:3.12-slim`, runs migrations on start.
- `Dockerfile.frontend` — builds the React app and serves it via **Caddy**, which
  also reverse-proxies `/api/*` to the backend and gets **automatic HTTPS**
  (Let's Encrypt) for a real domain.
- `docker-compose.yml` — `db` (PostgreSQL, **no published port**), `backend`
  (internal only, screenshots + backups on a volume), `web` (Caddy, ports 80/443).
- `.env.production.example` — copy to `.env.production` and fill in secrets.

### Deploy (on a VPS or on-prem host with Docker)

```bash
cd deployment
cp .env.production.example .env.production   # then fill in real secrets
# Point your domain's DNS A record at the host, set DOMAIN in .env.production
docker compose --env-file .env.production up -d --build
```

Caddy obtains TLS automatically once `DOMAIN` resolves to the host. The app is then
at `https://<DOMAIN>`, the API at `https://<DOMAIN>/api/...`, and PostgreSQL is not
reachable from outside. Create the first admin:

```bash
docker compose exec backend python scripts/create_admin.py --email you@example.com --role owner
```

### Secrets

Generate strong values and keep them in `.env.production` (never committed):

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"                 # JWT_SECRET
python -c "import base64,os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"  # SCREENSHOT_KEY
```

Point agents' `server_url` at `https://<DOMAIN>/api`.

## Free-tier cloud option (pilot only)

If you want a zero-cost pilot and accept the caveats: host the **frontend on
Cloudflare Pages**, the **database on Neon**, the **backend on a free tier**
(accepting sleep), and **screenshots on a private R2/B2 bucket** (requires moving
screenshot storage from local disk to object storage — not yet implemented). This
is fine for a demo but **not recommended for production sensitive data** because of
sleep, ephemeral storage, and idle pauses.

## Local option

For development or a fully in-house deployment, run the same Compose stack on a
local machine (e.g. a spare PC). This keeps all data on-premises and costs nothing
but the hardware and power — often the best fit for sensitive company data.

## Monitoring and backups in production

- Point **UptimeRobot** (free) at `https://<DOMAIN>/api/health`.
- Schedule `scripts/backup.py` (daily) and copy the encrypted backup off-host to a
  private bucket. Test a restore periodically (see [backups.md](backups.md)).
- Schedule `scripts/retention_cleanup.py` (daily) to enforce retention.

## Staged rollout

1. **Local simulation** — run the stack locally; exercise login, enrollment,
   heartbeat, screenshots, and location with the simulated agent and one test
   device. (Done through Milestones 2–11.)
2. **Staging deploy** — deploy the Compose stack to the VPS/on-prem host with a
   real domain and TLS. Create an owner admin. Verify from outside the network.
3. **One pilot device** — enroll a single company Windows laptop via the installed
   agent pointed at the production URL. Watch health, usage, and alerts for a few
   days. Confirm the monitoring notice is visible to the device user.
4. **Small pilot group** — add 2–3 devices. Confirm reliability (no missed
   check-ins), storage growth, and that retention/backup jobs run.
5. **Full rollout** — enroll the remaining company devices. Keep the compatibility
   table current; only enable features proven on each platform.
6. **Operate** — monitor uptime, review the audit log and alerts, keep backups and
   restores tested, and rotate secrets periodically.

## Sources

- [Render free tier details](https://render.com/docs/free)
- [Neon pricing](https://neon.com/pricing)
- [Supabase pricing](https://supabase.com/pricing)
- [Cloudflare Pages limits](https://developers.cloudflare.com/pages/platform/limits/)
- [Cloudflare R2 pricing](https://developers.cloudflare.com/r2/pricing/)
- [Let's Encrypt](https://letsencrypt.org/)
- [Caddy automatic HTTPS](https://caddyserver.com/docs/automatic-https)
