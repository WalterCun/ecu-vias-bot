"""Bot settings — loaded from .env via pydantic-settings."""

from datetime import time
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    DEBUG: bool = False
    BASE_DIR: Path = Path(__file__).parent.parent.parent

    # Bot Telegram
    TELEGRAM_KEY_BOT: str = ""
    ID_ADMIN: int = 0

    # Admin IDs (comma-separated Telegram user IDs)
    ADMIN_IDS: str = ""

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # API cache
    VIA_CACHE_TTL: int = 60
    MAX_CONCURRENT_SENDS: int = 20

    # DB sync interval in seconds
    DB_SYNC_INTERVAL_SECONDS: int = 900

    # Web scraping / API
    URL_SCRAPPING_WEB: str = "https://ecu911.gob.ec"

    # Cache
    CACHE_NAME: str = "ecuavias.db"
    CACHE_TIME_EXPIRATION: int = 1800

    # Legacy DB
    DB_NAME: str = "ecuavias.db"
    DATABASE_URL: str = f"sqlite://{BASE_DIR / DB_NAME}"

    # Legacy sync
    SYNCDB_REFRESH_TIME: int = 5
    SYNCDB_TIME: int = 3600
    DAYS_TO_KEEP_DATA: str = "30"

    # Legacy UI labels
    CONTINUE_BUTTON: str = "CONTINUAR ✅"
    PROGRAMMING_DONE_BUTTON: str = "PROGRAMAR ✅"

    # Time options
    ONCE_A_DAY: dict[str, time] = {
        f"{hour % 12 or 12} {'AM' if hour < 12 else 'PM'}": time(hour=hour)
        for hour in range(24)
    }

    class Config:
        env_file = str(Path(__file__).parent.parent.parent / ".env")
        extra = "ignore"  # Ignore unknown env vars instead of crashing


settings = Settings()
