# Feature compatibility table

Tracks the **actual, tested** status of each feature per platform. A feature is
marked ✅ only after it is implemented **and** tested on that operating system.

Legend: ✅ working & tested · 🚧 in progress · 📋 planned · ❌ not supported on
platform · ❓ feasibility not yet confirmed

| Feature                         | Windows | Android | iOS   | Notes                                              |
| ------------------------------- | ------- | ------- | ----- | -------------------------------------------------- |
| Device enrollment / registration | ✅      | ❓      | ❓    | Windows agent enrolls via one-time secret (tested on Windows 11)               |
| Heartbeat / online status       | ✅      | 📋      | 📋    | Windows agent check-ins drive live status (tested on Windows 11)               |
| Device health (OS, disk, battery)| ✅      | 🚧      | 🚧    | Windows agent tested. Android (AMAPI) + iOS (MDM) inventory assessed; not live-tested |
| Mobile enrollment (supervised)   |  —      | 🚧      | 🚧    | Android AMAPI QR + iOS ABM/ADE assessed; need vendor accounts + devices         |
| Compliance / managed apps        |  —      | 🚧      | 🚧    | Android AMAPI + iOS MDM profiles assessed (scaffolded, not live-tested)          |
| Foreground app usage             | ✅      | ❓      | ❌    | Windows: app names + durations, idle excluded (tested). iOS MDM cannot do this  |
| Managed startup (auto-start)     | ✅      | 📋      | 📋    | Windows: visible per-user logon task, no admin needed (tested)                 |
| Agent crash recovery             | ✅      | 📋      | 📋    | Windows: supervisor restarts with backoff (tested)                             |
| Secure updates                   | 🚧      | 📋      | 📋    | Version reporting + "update available" done; auto self-update not yet          |
| Policy-controlled screenshots    | ✅      | ❌      | ❌    | Windows agent: scheduled/on-request, encrypted, retained (tested). Not via Android/iOS MDM |
| Authorized live remote support   | ✅      | ❌      | ❌    | Windows: authorized near-live snapshots + consent indicator (tested). Full-motion: integrate WebRTC/RustDesk |
| Location                         | ❓      | 🚧      | 🚧    | Android: AMAPI Lost Mode only. iOS: Managed Lost Mode, supervised only. No continuous GPS. Assessed, not live-tested |
| Remote lock / wipe               | ❓      | 🚧      | 🚧    | Android: AMAPI LOCK/WIPE. iOS: DeviceLock/EraseDevice via MDM. Assessed, not live-tested |

> This table starts almost entirely as 📋/❓ on purpose. Cells move to ✅ only
> after Milestone-by-milestone implementation and testing. Mobile capabilities
> depend on enrollment models and vendor terms that must be verified before any
> are promised.
