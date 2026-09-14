from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    app_name: str = "ApplyWise AI"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"

    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "applywise_ai"

    jwt_secret_key: str = (
        "development-secret-change-before-production"
    )
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    resume_upload_dir: Path = Path("uploads/resumes")
    max_resume_size_bytes: int = 5 * 1024 * 1024

    gemini_api_key: SecretStr | None = None
    gemini_model: str = "gemini-3.8-flash"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def database_url(self) -> URL:
        return URL.create(
            drivername="mysql+pymysql",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
            query={"charset": "utf8mb4"},
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()