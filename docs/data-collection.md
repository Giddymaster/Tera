# Data collection and access

This document records **exactly what data the system stores, when, and who can
access it.** It is updated as each milestone adds functionality. A feature that
is not listed here does not collect data yet.

## As of Milestone 2 (backend foundation)

No device agents exist yet, so **no employee activity, screenshots, location, or
device telemetry is collected.** The backend stores only:

| Data                     | When written                        | Contains                                                        | Who can read |
| ------------------------ | ----------------------------------- | --------------------------------------------------------------- | ------------ |
| Admin accounts           | When an admin is created            | Email, Argon2 password **hash** (never plaintext), role, timestamps | System; admins via future user-management UI |
| Device records           | When an admin registers a device    | Opaque device id, name, OS/type, assignee label, enrollment status, enrollment secret **hash** | Admins with `view_devices` |
| Audit log                | On login (success/failure) and device create/revoke/delete | Actor email, action, target, timestamp, client IP; **no passwords or secrets** | Admins (reporting UI in a later milestone) |

### Explicitly **not** stored

- Plaintext passwords (only Argon2 hashes).
- Plaintext device enrollment secrets (only hashes; the secret is shown to the
  admin once at creation).
- Any keystrokes, clipboard contents, screen contents, microphone audio, message
  contents, or browsing page contents. None of these are collected by any
  component in this milestone, and the project forbids covert collection of them.

## Future milestones

When agents are added, this table will be extended with: foreground application
names and durations, device health metrics, policy-controlled screenshots,
authorized remote-support sessions, and supported location data — each with its
collection schedule, retention period, and the permission required to view it.
Monitoring will be disclosed to device users, and sensitive content (passwords,
auth screens, private messages) will be excluded.
