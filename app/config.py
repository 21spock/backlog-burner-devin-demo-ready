from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    database_path: str = str(BASE_DIR / "app" / "data" / "backlog_burner.db")
    github_token: str = ""
    github_owner: str = ""
    github_repo: str = ""
    devin_api_key: str = ""
    devin_org_id: str = ""
    devin_api_base: str = "https://api.devin.ai/v3/organizations"
    slack_webhook_url: str = ""
    stale_days_threshold: int = Field(default=30, ge=1)
    max_parallel_runs: int = Field(default=3, ge=1)


@lru_cache
def get_settings() -> Settings:
    return Settings()
