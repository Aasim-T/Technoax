"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_ENV_FILE = _BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """Technoax application settings."""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="Technoax", description="API display name")
    app_version: str = Field(default="1.0.0", description="API version")
    debug: bool = Field(default=False, description="Enable debug mode")

    gemini_api_key: str = Field(
        default="",
        validation_alias="GEMINI_API_KEY",
        description="Google Gemini API key from backend/.env",
    )
    gemini_model: str = Field(
        default="gemini-2.0-flash",
        validation_alias="GEMINI_MODEL",
        description="Gemini model identifier",
    )

    cors_origins: str = Field(
        default="*",
        description="Comma-separated list of allowed CORS origins",
    )

    @field_validator("gemini_api_key", mode="before")
    @classmethod
    def strip_gemini_api_key(cls, value: object) -> str:
        """Normalize API key loaded from GEMINI_API_KEY."""
        if value is None:
            return ""
        return str(value).strip()

    @field_validator("gemini_model", mode="before")
    @classmethod
    def strip_gemini_model(cls, value: object) -> str:
        if value is None:
            return "gemini-2.0-flash"
        return str(value).strip()

    @property
    def is_gemini_configured(self) -> bool:
        """True when a non-empty GEMINI_API_KEY is available."""
        print("GEMINI API KEY:", self.gemini_api_key)
        return bool(self.gemini_api_key)

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
