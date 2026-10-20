"""Application configuration.

Settings are loaded from environment variables (and a local ``.env`` file in
development). See ``.env.example`` at the project root for the full list.

Security rule enforced here: in production the app refuses to start without a
real ``JWT_SECRET``. In development we fall back to a random, in-memory secret
so you can run the app immediately, but tokens then become invalid on restart
(which is fine for local work).
"""

from __future__ import annotations

import secrets
import warnings
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Look for a .env file at the project root (one level above backend/).
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- Core app ----
    app_env: Literal["development", "production"] = "development"
    app_name: str = "Employee Device Manager"
    log_level: Literal["debug", "info", "warning", "error"] = "info"

    # ---- Server ----
    backend_host: str = "127.0.0.1"
    backend_port: int = 8000
    cors_allow_origins: str = "http://localhost:5173"

    # ---- Database ----
    database_url: str = "sqlite+aiosqlite:///./dev.db"

    # ---- Security / auth ----
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = Field(default=15, ge=1)
    refresh_token_days: int = Field(default=7, ge=1)

    # Login rate limiting (per client IP).
    login_max_attempts: int = Field(default=5, ge=1)
    login_window_seconds: int = Field(default=300, ge=1)

    @field_validator("cors_allow_origins")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()

    @property
    def cors_origins_list(self) -> list[str]:
        """CORS origins as a clean list (comma-separated in the env var)."""
        return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @model_validator(mode="after")
    def _enforce_secret(self) -> "Settings":
        if not self.jwt_secret:
            if self.is_production:
                raise ValueError(
                    "JWT_SECRET must be set in production. Generate one with: "
                    'python -c "import secrets; print(secrets.token_urlsafe(48))"'
                )
            # Development convenience: ephemeral secret, invalid across restarts.
            object.__setattr__(self, "jwt_secret", secrets.token_urlsafe(48))
            warnings.warn(
                "JWT_SECRET is not set; using a temporary development secret. "
                "Tokens will be invalidated when the server restarts.",
                stacklevel=2,
            )
        return self


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance (read once per process)."""
    return Settings()
