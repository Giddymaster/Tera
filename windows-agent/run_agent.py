"""Entry point for the Windows monitoring agent.

Usage (from the windows-agent/ directory):

    python run_agent.py --config config.json

Create config.json from config.example.json first and fill in the server URL,
device id, and one-time enrollment secret (obtained when an admin registers the
device in the dashboard).
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Make the `agent` package importable when run as a plain script.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent.runner import run  # noqa: E402
from agent.supervisor import supervise  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Employee Device Manager agent.")
    parser.add_argument("--config", default="config.json", help="path to config.json")
    parser.add_argument(
        "--log-file", default="agent.log", help="path to the agent log file"
    )
    parser.add_argument(
        "--supervise",
        action="store_true",
        help="auto-restart the agent if it exits unexpectedly (used by the "
        "installed logon task)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(args.log_file, encoding="utf-8"),
        ],
    )
    if args.supervise:
        return supervise(args.config)
    return run(args.config)


if __name__ == "__main__":
    raise SystemExit(main())
