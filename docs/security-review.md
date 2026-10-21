# Security review (Milestone 11)

A focused review of authentication, authorization, data protection, and the API
surface, with mitigations and residual risks. Date: 2026-10-21.

## Authentication

| Item | Status |
| --- | --- |
| Passwords hashed with Argon2; never stored or logged in plaintext | ✅ |
| Login rate-limited per IP; identical error for unknown email / wrong password (no user enumeration) | ✅ |
| Successful and failed logins are audit-logged (no password in the log) | ✅ |
| JWT access tokens short-lived (15 min); refresh (7 d); device tokens long-lived with revocation via device status | ✅ |
| `JWT_SECRET` required in production; dev uses a temporary secret with a warning | ✅ |
| No default production passwords; `create_admin` enforces a minimum length | ✅ |

**Residual / accepted:** access tokens are stateless, so deactivating an admin
does not invalidate an already-issued access token until it expires (≤15 min).
Device revocation is immediate (enrollment status is checked on every request).
MFA is not implemented yet. A token-version/JTI blocklist for instant revocation
is a documented future improvement.

## Authorization

| Item | Status |
| --- | --- |
| Role-based permissions; every protected endpoint requires a specific permission | ✅ |
| Admin tokens and device tokens are distinct types; each is rejected on the other's endpoints | ✅ |
| Revoked devices cannot enroll or submit data | ✅ |
| Screenshot viewing, policy changes, live sessions, and location each gated by the right permission | ✅ |

## Data protection

| Item | Status |
| --- | --- |
| Screenshots encrypted at rest (Fernet/AES); decrypted only for authorized viewing | ✅ |
| Database backups encrypted at rest | ✅ |
| Secrets kept out of Git (.env, keys, config, service-account JSON, DB, screenshots all gitignored) | ✅ |
| Input validated with Pydantic; per-path request-size limits | ✅ |
| SQL via SQLAlchemy parameterized queries only (no string-built SQL) → SQL injection mitigated | ✅ |
| Security headers: CSP, X-Frame-Options DENY, X-Content-Type-Options nosniff, Referrer-Policy; HSTS in production | ✅ |
| CORS restricted to configured origins (not wildcard with credentials) | ✅ |
| Audit logging of admin and device actions; no secrets logged | ✅ |
| Retention + permanent deletion for screenshots, location, usage, and audit | ✅ |
| Deleting a device removes all associated rows (ON DELETE CASCADE) and its screenshot files on disk | ✅ |

**CSRF:** the API authenticates with a Bearer token in the `Authorization`
header, not cookies, so there is no ambient credential for a cross-site request
to abuse. CSRF protection is therefore not applicable as built. If cookie-based
auth is ever added, CSRF tokens must be added too.

## Transport

- Production must be served over HTTPS (deployment, Milestone 12). HSTS is set in
  production responses. Development runs on `http://localhost` only.
- Do not expose PostgreSQL to the public internet; do not use public,
  unauthenticated storage for screenshots or backups.

## Residual risks (accepted for now, tracked)

1. Stateless token revocation window (≤15 min for access tokens); no MFA yet.
2. SQLite in development; PostgreSQL in production — keep it private.
3. Backups are encrypted with the screenshot key in this prototype; production
   should use a dedicated backup key and off-site, access-controlled storage.
4. The Android/iOS management integrations are assessed and scaffolded but not
   live-tested (need vendor accounts and devices).
5. Secrets live in a local `.env` in development; production should use a secrets
   manager and rotate keys.
