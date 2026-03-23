"""Настройки приложения (чтение из переменных окружения / .env)."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки сервиса."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://app:app@db:5432/app"
    bank_api_base_url: str = "http://bank.api"
    bank_api_timeout_s: float = 5.0


settings = Settings()
"""Глобальный экземпляр настроек (singleton)."""
