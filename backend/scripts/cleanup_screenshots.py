"""Delete screenshots whose retention period has passed.

Screenshots are also purged opportunistically on each new upload, but running
this on a schedule (e.g. a daily task) guarantees cleanup even for idle devices.

Usage (backend/ dir, venv active):

    python scripts/cleanup_screenshots.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal  # noqa: E402
from app.core.screenshots import delete_expired  # noqa: E402


async def main() -> int:
    async with SessionLocal() as session:
        removed = await delete_expired(session)
    print(f"Deleted {removed} expired screenshot(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
