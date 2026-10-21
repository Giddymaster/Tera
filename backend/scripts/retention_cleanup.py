"""Run every data-retention cleanup (screenshots, location, usage, audit).

Run this on a schedule (e.g. a daily task) so data is deleted per the configured
retention even for idle devices.

Usage (backend/ dir, venv active):

    python scripts/retention_cleanup.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal  # noqa: E402
from app.core.retention import run_all  # noqa: E402


async def main() -> int:
    async with SessionLocal() as session:
        result = await run_all(session)
    for name, count in result.items():
        print(f"{name}: deleted {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
