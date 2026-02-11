"""
Application configuration using Pydantic Settings.

Loads environment variables from .env file and provides type-safe access
to all configuration values throughout the application.
"""

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Get the directory where this config file lives (backend/app/)
# Then go up one level to backend/ where .env should be
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="myHealth", description="Application name")
    app_env: str = Field(default="development", description="Environment (development/staging/production)")
    debug: bool = Field(default=True, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json/text)")

    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")

    # Supabase
    supabase_url: str = Field(..., description="Supabase project URL")
    supabase_anon_key: str = Field(..., description="Supabase anonymous key")
    supabase_service_role_key: str = Field(..., description="Supabase service role key")

    # Security
    secret_key: str = Field(..., description="Secret key for additional encryption")
    cors_origins: List[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"],
        description="Allowed CORS origins",
    )

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    trusted_proxy_count: int = Field(
        default=0,
        description="Number of trusted reverse proxies. 0 = direct connection (ignores X-Forwarded-For)"
    )

    # Whoop OAuth Configuration
    whoop_client_id: str = Field(default="", description="Whoop OAuth client ID")
    whoop_client_secret: str = Field(default="", description="Whoop OAuth client secret")
    whoop_redirect_uri: str = Field(
        default="http://localhost:8000/api/v1/whoop/callback",
        description="Whoop OAuth redirect URI"
    )
    whoop_api_base_url: str = Field(
        default="https://api.prod.whoop.com/developer",
        description="Whoop API base URL"
    )
    whoop_auth_url: str = Field(
        default="https://api.prod.whoop.com/oauth/oauth2/auth",
        description="Whoop OAuth authorization URL"
    )
    whoop_token_url: str = Field(
        default="https://api.prod.whoop.com/oauth/oauth2/token",
        description="Whoop OAuth token URL"
    )

    # Token Encryption
    encryption_key: str = Field(default="", description="Fernet encryption key for token storage")

    # Frontend URL (for OAuth redirects)
    frontend_url: str = Field(
        default="http://localhost:5173",
        description="Frontend application URL"
    )

    # USDA FoodData Central API
    usda_api_key: str = Field(default="", description="USDA FoodData Central API key")
    usda_api_base_url: str = Field(
        default="https://api.nal.usda.gov/fdc/v1",
        description="USDA FoodData Central API base URL"
    )

    # AWS Bedrock Configuration
    aws_region: str = Field(default="us-east-1", description="AWS region for Bedrock")
    aws_access_key_id: str = Field(default="", description="AWS access key ID")
    aws_secret_access_key: str = Field(default="", description="AWS secret access key")
    bedrock_model_id: str = Field(
        default="us.anthropic.claude-3-5-haiku-20241022-v1:0",
        description="AWS Bedrock model ID (cross-region inference)"
    )

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env == "development"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()
