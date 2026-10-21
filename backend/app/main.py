"""FastAPI application entry point.

Run locally with:
    uvicorn app.main:app --reload
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.api import (
    agent,
    android,
    apple,
    audit,
    auth,
    devices,
    location,
    reports,
    screenshots,
    sessions,
)
from app.core.config import get_settings
from app.core.database import create_all

settings = get_settings()

# Reject oversized request bodies early. Most endpoints are tiny (1 MB cap); the
# one large payload is the screenshot upload, which gets a higher cap (base64
# inflates bytes by ~1.37x, plus JSON overhead).
MAX_REQUEST_BYTES = 1_000_000  # 1 MB default
SCREENSHOT_UPLOAD_PATH = "/agent/screenshot"
MAX_SCREENSHOT_REQUEST_BYTES = int(settings.max_screenshot_bytes * 1.6)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    # In development we create tables automatically so the app runs out of the
    # box. Production relies on Alembic migrations instead.
    if not settings.is_production:
        await create_all()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def limit_body_size(request: Request, call_next):
        limit = (
            MAX_SCREENSHOT_REQUEST_BYTES
            if request.url.path == SCREENSHOT_UPLOAD_PATH
            else MAX_REQUEST_BYTES
        )
        content_length = request.headers.get("content-length")
        if content_length is not None and int(content_length) > limit:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"detail": "Request body too large"},
            )
        return await call_next(request)

    app.include_router(auth.router)
    app.include_router(devices.router)
    app.include_router(agent.router)
    app.include_router(audit.router)
    app.include_router(screenshots.router)
    app.include_router(sessions.router)
    app.include_router(android.router)
    app.include_router(apple.router)
    app.include_router(location.router)
    app.include_router(reports.router)

    @app.get("/health", tags=["meta"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    @app.get("/meta", tags=["meta"])
    async def meta() -> dict[str, str]:
        # Version info only; not sensitive. Used by the dashboard to flag
        # devices whose agent is behind the latest published version.
        return {
            "server_version": __version__,
            "latest_agent_version": settings.agent_latest_version,
        }

    @app.get("/", tags=["meta"])
    async def root() -> dict[str, str]:
        return {"name": settings.app_name, "docs": "/docs", "health": "/health"}

    return app


app = create_app()
