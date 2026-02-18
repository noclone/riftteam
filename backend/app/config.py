from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Backend configuration loaded from environment variables and .env file."""

    database_url: str = "postgresql+asyncpg://riftteam:riftteam@localhost:5433/riftteam"
    riot_api_key: str = ""
    app_url: str = "http://localhost:5173"
    api_url: str = "http://localhost:8000"
    secret_key: str = "change-me-in-production"
    bot_api_secret: str = "change-bot-secret-in-production"

    model_config = {"env_file": "../.env", "extra": "ignore"}


settings = Settings()
