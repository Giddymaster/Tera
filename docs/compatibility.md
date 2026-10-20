# Feature compatibility table

Tracks the **actual, tested** status of each feature per platform. A feature is
marked ✅ only after it is implemented **and** tested on that operating system.

Legend: ✅ working & tested · 🚧 in progress · 📋 planned · ❌ not supported on
platform · ❓ feasibility not yet confirmed

| Feature                         | Windows | Android | iOS   | Notes                                              |
| ------------------------------- | ------- | ------- | ----- | -------------------------------------------------- |
| Device enrollment / registration | ✅      | ❓      | ❓    | Windows agent enrolls via one-time secret (tested on Windows 11)               |
| Heartbeat / online status       | ✅      | 📋      | 📋    | Windows agent check-ins drive live status (tested on Windows 11)               |
| Device health (OS, disk, battery)| ✅      | ❓      | ❓    | Windows agent reports OS/disk/battery (tested on Windows 11)                    |
| Foreground app usage             | ✅      | ❓      | ❌    | Windows: app names + durations, idle excluded (tested). iOS MDM cannot do this  |
| Policy-controlled screenshots    | 📋      | ❌      | ❌    | Not available via standard Android/iOS MDM         |
| Authorized live remote support   | 📋      | ❓      | ❌    | Use an established, maintained remote-support tech |
| Location                         | ❓      | ❓      | ❓    | Depends on enrollment model / permissions          |
| Remote lock / wipe               | ❓      | ❓      | ❓    | Requires supported MDM enrollment                  |

> This table starts almost entirely as 📋/❓ on purpose. Cells move to ✅ only
> after Milestone-by-milestone implementation and testing. Mobile capabilities
> depend on enrollment models and vendor terms that must be verified before any
> are promised.
