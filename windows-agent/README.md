# windows-agent

A prototype Windows monitoring agent for the Employee Device Manager. It runs on
a company-owned laptop and reports:

- **Device health** — OS version, free/total disk space, battery and power status.
- **Foreground application usage** — the **name** of the app in focus and how long
  it is used, aggregated per app per day. Idle time (no keyboard/mouse) is not
  counted.

## What it does NOT collect

By design, the agent never records keystrokes, clipboard contents, window titles,
URLs, page contents, screenshots, microphone, or any file contents. It reports
application names and durations only. A monitoring notice is printed when it
starts.

## Requirements

- Windows 10/11
- Python 3.11+ (tested on 3.14)

## Setup

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
Managed startup as a Windows service, signed installers, and secure auto-update
are **Milestone 6**. Until then the agent runs in a console you start manually.
Foreground detection and battery status require a real Windows desktop session;
they return nothing on a server or headless environment.
