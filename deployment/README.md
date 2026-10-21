# deployment

Self-hosted production stack for the Employee Device Manager. See the full guide,
hosting comparison, and staged rollout plan in
[../docs/deployment.md](../docs/deployment.md).

## Files

- `Dockerfile.backend` — FastAPI API (Python 3.12); runs migrations on start.
- `Dockerfile.frontend` — builds the React app and serves it via Caddy, which also
  reverse-proxies `/api/*` to the backend and provides automatic HTTPS.
- `Caddyfile` — Caddy config (SPA + API proxy + TLS).
- `entrypoint.sh` — backend start script (`alembic upgrade head` then uvicorn).
- `docker-compose.yml` — `db` (PostgreSQL, private), `backend` (private), `web`
  (Caddy, ports 80/443).
- `.env.production.example` — copy to `.env.production` and fill in secrets.

## Quick start (on a host with Docker)

```bash
cd deployment
cp .env.production.example .env.production   # then fill in secrets + DOMAIN
docker compose --env-file .env.production up -d --build
docker compose exec backend python scripts/create_admin.py --email you@example.com --role owner
```

PostgreSQL is **not** published to the host — it is reachable only on the internal
Docker network. Agents point their `server_url` at `https://<DOMAIN>/api`.
