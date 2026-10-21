from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_HOST: str = "35.219.95.135"
    DB_PORT: int = 5435
    DB_USER: str = "jxb_ai_dev"
    DB_PASS: str = "Hidup_Jokowi"
    DB_NAME: str = "jxb_ai_dev"

    LLM_API_URL: str = "http://35.219.95.135:20128/v1/responses"
    LLM_MODEL: str = "jxb"
    LLM_API_KEY: str = ""
    LLM_TIMEOUT_SECONDS: int = 120
    LLM_MAX_RETRIES: int = 2
    LLM_MAX_ANSWER_CHARS: int = 2500

    GUARDRAILS_ENABLED: bool = True
    LLM_SUMMARY_MAX_ROWS: int = 50

    POOL_MIN_SIZE: int = 2
    POOL_MAX_SIZE: int = 10

    LLM_CHAT_ONLY: bool = True

    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASS}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()