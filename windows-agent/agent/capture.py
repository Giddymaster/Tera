"""Capture the screen as a compressed JPEG.

Returns downscaled, quality-reduced JPEG bytes to keep uploads small. Returns
None when capture is unavailable (missing libraries or no desktop session), so
the agent degrades gracefully instead of crashing.
"""

from __future__ import annotations

import io

try:
    import mss
    from PIL import Image
except ImportError:  # pragma: no cover - optional deps
    mss = None  # type: ignore[assignment]
    Image = None  # type: ignore[assignment]


def capture_jpeg(max_width: int = 1280, quality: int = 45) -> tuple[bytes, int, int] | None:
    if mss is None or Image is None:
        return None
    try:
        with mss.mss() as sct:
            monitor = sct.monitors[1]  # primary virtual screen
            raw = sct.grab(monitor)
            img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
    except Exception:  # noqa: BLE001 - capture can fail on locked/headless sessions
        return None

    width, height = img.size
    if width > max_width:
        new_height = max(1, int(height * max_width / width))
        img = img.resize((max_width, new_height))
        width, height = img.size

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    return buf.getvalue(), width, height
