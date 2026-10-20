"""Create an administrator account.

Usage (from the backend/ directory, with the venv active):

    python scripts/create_admin.py --email you@example.com --role owner

You will be prompted for a password (input is hidden and never logged). For
non-interactive use, set ADMIN_PASSWORD in the environment instead.

Roles: owner | admin | viewer
"""

from __future__ import annotations

import argparse
import asyncio
import getpass
import os
import sys
from pathlib import Path

# Make the `app` package importable when run as a plain script.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from app.core.database import SessionLocal, create_all  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models.admin import Admin  # noqa: E402
from app.models.enums import Role  # noqa: E402


async def main() -> int:
    parser = argparse.ArgumentParser(description="Create an admin account.")
    parser.add_argument("--email", required=True)
    parser.add_argument(
        "--role", default="admin", choices=[r.value for r in Role]
    )
    args = parser.parse_args()

    email = args.email.lower().strip()
    password = os.environ.get("ADMIN_PASSWORD")
    if not password:
        password = getpass.getpass("Password: ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("Passwords do not match.", file=sys.stderr)
            return 1
    if len(password) < 10:
        print("Password must be at least 10 characters.", file=sys.stderr)
        return 1

    await create_all()
    async with SessionLocal() as session:
        existing = await session.execute(select(Admin).where(Admin.email == email))
        if existing.scalar_one_or_none() is not None:
            print(f"An admin with email {email} already exists.", file=sys.stderr)
            return 1
        admin = Admin(
            email=email,
            hashed_password=hash_password(password),
            role=Role(args.role),
        )
        session.add(admin)
        await session.commit()
        print(f"Created {args.role} admin: {email}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
