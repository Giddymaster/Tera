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

## Added in Milestone 4 (device enrollment and heartbeat)

Devices can now enroll and check in. This adds the following, still with no
employee activity, screenshots, or location collection:

| Data                     | When written                         | Contains                                              | Who can read |
| ------------------------ | ------------------------------------ | ----------------------------------------------------- | ------------ |
| Device check-in time     | On each agent heartbeat              | `last_seen_at` timestamp                              | Admins with `view_devices` |
| Reported device version  | On heartbeat (when the agent sends it) | Agent version, OS version strings                   | Admins with `view_devices` |
| Enrollment events        | On enroll success/failure            | Device id, client IP, timestamp (no secret stored)   | Admins with `view_reports` |

The heartbeat payload in this milestone carries only the agent version and OS
version. Richer device health (disk, battery, security status) arrives with the
Windows agent in Milestone 5 and will be added here then.

## Added in Milestone 5 (Windows agent)

The Windows agent now reports real data from a laptop. Collection is limited to
work-relevant, non-sensitive information:

| Data                     | When written                         | Contains                                                  | Who can read |
| ------------------------ | ------------------------------------ | --------------------------------------------------------- | ------------ |
| Device health            | On each heartbeat (default every 60s) | OS version, free/total disk (system drive), battery % and power state | Admins with `view_devices` |
| Foreground app usage     | Flushed periodically (default every 120s) | Application **name** (e.g. `chrome.exe`) and active seconds, per app per day | Admins with `view_reports` |

### Explicitly **not** collected by the agent

Window titles, document names, URLs, page contents, keystrokes, clipboard,
screenshots, microphone, and file contents are never collected. Time while the
user is idle (no keyboard/mouse past a threshold) is not counted. The agent
prints a monitoring notice when it starts and identifies itself by agent version.

## Future milestones

When agents are added, this table will be extended with: foreground application
names and durations, device health metrics, policy-controlled screenshots,
authorized remote-support sessions, and supported location data — each with its
collection schedule, retention period, and the permission required to view it.
Monitoring will be disclosed to device users, and sensitive content (passwords,
auth screens, private messages) will be excluded.
