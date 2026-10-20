"""Simulate a device agent end-to-end against the running API.

This is a development/demo tool. It signs in as an admin, registers a new
device, enrolls it (consuming the one-time secret), then sends heartbeats so the
device shows as "Online" in the dashboard.

Usage (backend/ dir, venv active, server running):

    python scripts/simulate_agent.py --email admin@demo.local --password DemoPass12345

Options: --count N (heartbeats, default 10), --interval S (seconds, default 10),
--base-url URL (default http://127.0.0.1:8000).
"""

from __future__ import annotations

import argparse
import os
import sys
import time

import httpx


def main() -> int:
    parser = argparse.ArgumentParser(description="Simulate a device agent.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", default=os.environ.get("ADMIN_PASSWORD"))
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--interval", type=float, default=10.0)
    parser.add_argument("--name", default="Simulated Agent Laptop")
    args = parser.parse_args()

    if not args.password:
        print("Provide --password or set ADMIN_PASSWORD.", file=sys.stderr)
        return 1

    base = args.base_url.rstrip("/")
    with httpx.Client(base_url=base, timeout=10.0) as http:
        # 1. Admin login.
        r = http.post(
            "/auth/login", json={"email": args.email, "password": args.password}
        )
        if r.status_code != 200:
            print(f"Login failed ({r.status_code}): {r.text}", file=sys.stderr)
            return 1
        access = r.json()["access_token"]
        admin_auth = {"Authorization": f"Bearer {access}"}

        # 2. Register a device (admin), capturing the one-time secret.
        r = http.post(
            "/devices",
            json={"name": args.name, "os_type": "windows", "device_type": "laptop"},
            headers=admin_auth,
        )
        r.raise_for_status()
        created = r.json()
        uid = created["device"]["device_uid"]
        secret = created["enrollment_secret"]
        print(f"Registered device {uid}")

        # 3. Enroll (device side) -> device token.
        r = http.post(
            "/agent/enroll", json={"device_uid": uid, "enrollment_secret": secret}
        )
        r.raise_for_status()
        device_token = r.json()["device_token"]
        device_auth = {"Authorization": f"Bearer {device_token}"}
        print("Enrolled. Sending heartbeats... (Ctrl+C to stop)")

        # 4. Heartbeat loop.
        for i in range(1, args.count + 1):
            r = http.post(
                "/agent/heartbeat",
                json={"agent_version": "0.4.0", "os_version": "Windows 11 26H2"},
                headers=device_auth,
            )
            if r.status_code == 200:
                print(f"  heartbeat {i}/{args.count} ok")
            else:
                print(f"  heartbeat {i} failed ({r.status_code}): {r.text}")
                break
            if i < args.count:
                time.sleep(args.interval)

    print(f"Done. View it in the dashboard: {uid}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nStopped.")
