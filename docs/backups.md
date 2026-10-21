# Backups and recovery

Database backups are **encrypted at rest**. The backup file is a secret: store it
in access-controlled, off-site storage and never commit it (the `backups/`
directory is gitignored).

## Create a backup (SQLite / development)

From the `backend/` directory with the venv active:

```bash
python scripts/backup.py
```

This writes `backups/edm-backup-<timestamp>.db.enc` (a consistent snapshot taken
with SQLite `VACUUM INTO`, then encrypted) and prunes old backups beyond
`BACKUP_KEEP` (default 14). Schedule it (e.g. a daily Task Scheduler job or cron).

## Restore a backup

```bash
python scripts/restore.py --file backups/edm-backup-<timestamp>.db.enc --out restored.db
```

Restore writes to a **new** file by default; it does not overwrite the live
database. To put it into service: stop the server, back up the current `dev.db`,
replace it with `restored.db`, then start the server. Verify login and the device
list before relying on it.

## Key management

The backup is encrypted with the `SCREENSHOT_KEY`. **If you lose that key, the
backup cannot be decrypted.** Keep the key in a secrets manager, separate from the
backups themselves. In production, prefer a dedicated backup key.

## Production (PostgreSQL)

Use `pg_dump` piped through encryption, for example:

```bash
pg_dump "$DATABASE_URL" | age -r <recipient> > edm-backup-$(date -u +%Y%m%dT%H%M%SZ).sql.age
```

Restore with the matching decrypt + `psql`. Many managed Postgres providers also
offer automated, point-in-time backups — enable those and verify a restore.

## What to test

Periodically perform a **test restore** into a throwaway database and confirm the
app starts and data looks correct. A backup you have never restored is not a
backup you can rely on.
