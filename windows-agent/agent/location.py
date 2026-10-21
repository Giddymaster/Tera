"""Best-effort, permission-based device location.

Most laptops have no GPS, and we never invent coordinates. This returns one of:
- {"status": "ok", "latitude", "longitude", "accuracy_m"} when a real fix is
  obtained (requires the optional `winsdk` package and the user's location
  permission);
- {"status": "permission_restricted"} when location access is denied;
- {"status": "unavailable"} when no provider/permission is available.

Location is only collected on an admin request or a slow interval (never
continuous), controlled by the backend policy.
"""

from __future__ import annotations


def collect_location() -> dict:
    try:
        import asyncio

        from winsdk.windows.devices.geolocation import Geolocator  # type: ignore
    except Exception:  # noqa: BLE001 - winsdk not installed / not on Windows
        return {"status": "unavailable"}

    async def _get() -> dict:
        locator = Geolocator()
        pos = await locator.get_geoposition_async()
        coord = pos.coordinate
        point = coord.point.position
        return {
            "status": "ok",
            "latitude": float(point.latitude),
            "longitude": float(point.longitude),
            "accuracy_m": float(coord.accuracy) if coord.accuracy else None,
            "source": "windows_agent",
        }

    try:
        return asyncio.run(_get())
    except Exception as exc:  # noqa: BLE001 - map access errors to a clear status
        message = str(exc).lower()
        if "denied" in message or "access" in message or "unauthorized" in message:
            return {"status": "permission_restricted"}
        return {"status": "unavailable"}
