# windows-agent

A prototype Windows monitoring agent for the Employee Device Manager. It runs on
a company-owned laptop and reports:

- **Device health** — OS version, free/total disk space, battery and power status.
- **Foreground application usage** — the **name** of the app in focus and how long
  it is used, aggregated per app per day. Idle time (no keyboard/mouse) is not
  counted.

It can also capture **screenshots** and act as the device side of a **live
remote-support session**, but only under the controls described below.

## What it does NOT collect

By design, the agent never records keystrokes, clipboard contents, window titles,
URLs, page contents, microphone, or any file contents. For app usage it reports
application names and durations only. A monitoring notice is printed when it
starts.

## Screenshots and remote support (Milestone 7)

- Screenshots are captured **only** when the per-device policy (set by an admin in
  the dashboard) enables them, when an admin requests one, or while a live-support
  session is active. When monitoring is disabled, nothing is captured.
- Images are downscaled and compressed, sent to the backend, and **encrypted at
  rest** there. The agent keeps no local copy.
- An **excluded-apps** list in the policy skips capture while those apps are in
  the foreground (best-effort privacy for password managers etc.).
- During a live session the agent logs a visible **"session active"** notice each
  cycle, naming that an administrator is viewing the screen.
- Live support is **authorized near-live snapshots**, not full-motion video and
  not remote control. These need a desktop session; they do nothing headless.

## Requirements

- Windows 10/11
- Python 3.11+ (tested on 3.14)

## Quick install (recommended)

On the Windows laptop, register the device in the dashboard (**Add device**), then
copy the **one-command install** it shows and run it in PowerShell. It downloads the
agent, sets it up, writes the config, and auto-starts it — no git or manual editing.

Prerequisite: Python 3.11+ on the laptop. If it's missing:

```bash
winget install -e --id Python.Python.3.12
```

The command from the dashboard looks like this (values filled in for you):

```bash
$env:TERA_UID="dev_..."; $env:TERA_SECRET="..."; $env:TERA_URL="https://your-domain/api"; irm https://raw.githubusercontent.com/Giddymaster/Tera/main/windows-agent/bootstrap.ps1 | iex
```

The device appears **Online** in the dashboard within a minute. Remove it later with
`%LOCALAPPDATA%\TeraAgent\uninstall.ps1`.

## Manual setup (advanced)

From the `windows-agent/` directory:

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Register the device and configure

1. In the dashboard (as an admin), register a device. You receive a **device id**
   (`dev_...`) and a **one-time enrollment secret** shown once.
2. Copy the config template and fill it in:

   ```bash
   Copy-Item config.example.json config.json
   ```

   Set `server_url`, `device_uid`, and `enrollment_secret` in `config.json`.
   **`config.json` is gitignored — never commit it.**

## Run

```bash
python run_agent.py --config config.json
```

On first run the agent enrolls (trading the secret for a device token stored in
`.agent_state.json`) and then checks in on a schedule. Stop it with Ctrl+C; it
flushes any pending usage before exiting.

## How reliability works

- Usage reports that fail to send are queued to `.agent_state.json` and retried
  on the next cycle, so short outages do not lose data.
- Heartbeats are best-effort and retried on the next interval.
- All network errors are caught; the agent keeps running through outages.

## Managed startup (auto-start at logon)

To have the agent start automatically after sign-in/reboot, install it as a
per-user scheduled task (no administrator rights required):

```bash
.\install.ps1
```

This registers a task that launches the agent in **supervise** mode at logon. The
task is **visible** in Task Scheduler and in Task Manager > Startup - the agent is
not hidden and uses no covert persistence. Remove it with:

```bash
.\uninstall.ps1          # removes the task
.\uninstall.ps1 -Purge   # also deletes the stored device token
```

## Crash recovery

Supervise mode (`run_agent.py --supervise`, used by the installed task) restarts
the agent with exponential backoff if it exits unexpectedly, and the installed
task also carries Windows' own restart-on-failure setting. It does **not** restart
after a clean stop or when the device has been **revoked** (a revoked device's
check-in is rejected and the agent stops itself).

## Updates

On each check-in the backend reports the latest published agent version. If this
agent is behind, it logs a notice and the dashboard shows an "Update available"
badge on the device. Applying an update is currently a manual/admin step (replace
the files and restart the task). Automatic, signature-verified self-update is a
deliberate future step, not yet implemented.

## Configuration

| Key                         | Meaning                                  | Default |
| --------------------------- | ---------------------------------------- | ------- |
| `server_url`                | Backend base URL                         | —       |
| `device_uid`                | Device id from the dashboard             | —       |
| `enrollment_secret`         | One-time secret from the dashboard       | —       |
| `heartbeat_interval_seconds`| How often to report health               | 60      |
| `usage_flush_interval_seconds`| How often to send usage                | 120     |
| `sample_interval_seconds`   | How often to sample the foreground app   | 5       |

## Status and limitations

This is a **prototype**, suitable for development and a supervised test laptop.
Managed startup, crash recovery, version reporting, and admin-controlled uninstall
are implemented (Milestone 6). Still future: a signed installer package and
automatic, signature-verified self-update. Foreground detection and battery status
require a real Windows desktop session; they return nothing on a server or
headless environment.
