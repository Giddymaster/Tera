"""Seed the database with simulated demo devices for the dashboard.

These are fake records so the dashboard has realistic data to show before any
real device agent exists. They do not represent real devices and collect no
data.

Usage (from the backend/ directory, venv active):

    python scripts/seed_demo.py --yes

``--yes`` is required because the script first deletes all existing device rows
so repeated runs stay clean. Admin accounts are NOT touched; create one with
scripts/create_admin.py so you can log in.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import delete, func, select  # noqa: E402

from app.core.database import SessionLocal, create_all  # noqa: E402
from app.core.security import (  # noqa: E402
    generate_device_uid,
    generate_enrollment_secret,
    hash_secret,
)
from app.models.device import Device  # noqa: E402
from app.models.enums import DeviceType, EnrollmentStatus, OSType  # noqa: E402


def _ago(**kwargs: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(**kwargs)


# (name, os, type, assignee, status, last_seen) — last_seen None means no check-in.
DEMO = [
    ("Reception Laptop", OSType.WINDOWS, DeviceType.LAPTOP, "Front Desk", EnrollmentStatus.ENROLLED, _ago(seconds=20)),
    ("Sales Laptop", OSType.WINDOWS, DeviceType.LAPTOP, "A. Rivera", EnrollmentStatus.ENROLLED, _ago(minutes=2)),
    ("Manager iPhone", OSType.IOS, DeviceType.PHONE, "J. Okoro", EnrollmentStatus.ENROLLED, _ago(minutes=1)),
    ("Warehouse Tablet", OSType.ANDROID, DeviceType.TABLET, "Warehouse", EnrollmentStatus.ENROLLED, _ago(minutes=35)),
    ("Field Phone 1", OSType.ANDROID, DeviceType.PHONE, "Field Team", EnrollmentStatus.ENROLLED, _ago(hours=3)),
    ("New Laptop (unboxed)", OSType.WINDOWS, DeviceType.LAPTOP, None, EnrollmentStatus.PENDING, None),
    ("Retired Phone", OSType.ANDROID, DeviceType.PHONE, "Returned", EnrollmentStatus.REVOKED, _ago(days=9)),
]


async def main() -> int:
    parser = argparse.ArgumentParser(description="Seed demo devices.")
    parser.add_argument(
        "--yes", action="store_true", help="confirm deleting existing device rows"
    )
    args = parser.parse_args()

    await create_all()
    async with SessionLocal() as session:
        existing = await session.scalar(select(func.count()).select_from(Device))
        if existing and not args.yes:
            print(
                f"{existing} device(s) already exist. Re-run with --yes to replace "
                "them with the demo set.",
                file=sys.stderr,
            )
            return 1

        await session.execute(delete(Device))
        for name, os_type, dtype, assignee, status, last_seen in DEMO:
            session.add(
                Device(
                    device_uid=generate_device_uid(),
                    name=name,
                    os_type=os_type,
                    device_type=dtype,
                    assigned_to=assignee,
                    enrollment_status=status,
                    enrollment_secret_hash=hash_secret(generate_enrollment_secret()),
                    last_seen_at=last_seen,
                )
            )
        await session.commit()
        print(f"Seeded {len(DEMO)} demo devices.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
