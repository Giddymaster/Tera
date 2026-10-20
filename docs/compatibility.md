# Feature compatibility table

Tracks the **actual, tested** status of each feature per platform. A feature is
marked ✅ only after it is implemented **and** tested on that operating system.

Legend: ✅ working & tested · 🚧 in progress · 📋 planned · ❌ not supported on
platform · ❓ feasibility not yet confirmed

| Feature                         | Windows | Android | iOS   | Notes                                              |
| ------------------------------- | ------- | ------- | ----- | -------------------------------------------------- |
| Device enrollment / registration | 🚧      | ❓      | ❓    | Backend enroll API done + tested via simulated agent; real Windows agent in M5 |
| Heartbeat / online status       | 🚧      | 📋      | 📋    | Backend heartbeat + live status done + tested via simulated agent              |
| Device health (OS, disk, battery)| 📋      | ❓      | ❓    |                                                    |
| Foreground app usage             | 📋      | ❓      | ❌    | iOS MDM does not expose per-app foreground usage   |
| Policy-controlled screenshots    | 📋      | ❌      | ❌    | Not available via standard Android/iOS MDM         |
| Authorized live remote support   | 📋      | ❓      | ❌    | Use an established, maintained remote-support tech |
| Location                         | ❓      | ❓      | ❓    | Depends on enrollment model / permissions          |
| Remote lock / wipe               | ❓      | ❓      | ❓    | Requires supported MDM enrollment                  |

> This table starts almost entirely as 📋/❓ on purpose. Cells move to ✅ only
> after Milestone-by-milestone implementation and testing. Mobile capabilities
> depend on enrollment models and vendor terms that must be verified before any
> are promised.
