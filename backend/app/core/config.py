from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.limits import MAX_BODY_BYTES


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "SenimRadar AI"
    environment: str = "development"
    api_prefix: str = "/api/v1"
    database_url: str = "mysql+pymysql://senimradar@127.0.0.1:3306/senimradar_ai?charset=utf8mb4"
    cors_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:5174,http://127.0.0.1:5174"
    )
    rate_limit_per_minute: int = 120
    max_body_bytes: int = MAX_BODY_BYTES

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
