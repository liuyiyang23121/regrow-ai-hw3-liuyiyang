from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "ReGrow AI"
    API_PREFIX: str = "/api"

    OPENAI_API_KEY: str | None = None
    OPENAI_BASE_URL: str | None = None
    MODEL_NAME: str = "gpt-4.1-mini"

    TOKEN_BUDGET_PER_SESSION: int = 20_000
    COST_LIMIT_RMB: float = 5.0
    MAX_AUTO_RETRIES: int = 2
    HITL_AUDIENCE_THRESHOLD: int = 50_000
    STEP_DELAY_SECONDS: float = 0.35

    BASE_DIR: Path = Path(__file__).resolve().parents[2]
    DATABASE_PATH: Path = BASE_DIR / "data" / "regrow.db"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
