"""src/config/settings.py"""
from datetime import time
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Settings class used for managing configuration settings.

    Attributes:
        DEBUG (bool): A flag indicating if the debug mode is enabled.
        LOCALES_PATH (str): Path for locale files.
        MODERATOR (int): Index for the moderator type.
        SUBSCRIPTION (int): Index for the subscription type.
        NOTIFICATIONS (int): Index for the notification type.
        ALARM_NOTIFICATIONS (int): Index for the alarm notifications type.
        UNSUBSCRIPTION (int): Index for the unsubscription type.
        CONFIG (int"""
    DEBUG: bool
    BASE_DIR: Path = Path(__file__).parent.parent

    # Fluid
    LOCALES_PATH: Path = BASE_DIR / 'src' / 'controller' / 'languages' / 'langs'

    # States indexes for conversation handler
    MODERATOR: int = 0
    SUBSCRIPTION: int = 1
    NOTIFICATIONS: int = 2
    ALARM_NOTIFICATIONS: int = 3
    UNSUBSCRIPTION: int = 4
    CONFIG: int = 5
    CANCEL: int = 6
    UNSUBSCRIBE_FAIL: int = 7

    DB_NAME: str = 'ecuavias.db'
    DATABASE_URL: str = f'sqlite://{BASE_DIR / DB_NAME}'
    REDIS_URL: str = 'redis://localhost:6379/0'  # Opcional

    # Bot Telegram
    TELEGRAM_KEY_BOT: str
    ID_ADMIN: int

    # Web Scrapping
    URL_SCRAPPING_WEB: str
    DAYS_TO_KEEP_DATA: str

    # Cache Requests
    CACHE_NAME:str
    CACHE_TIME_EXPIRATION: int = 1800

    # consts
    ONCE_A_DAY: dict[str, time] = {
        f"{hour % 12 or 12} {'AM' if hour < 12 else 'PM'}": time(hour=hour) for hour in range(24)
    }

    # Sync DB
    SYNCDB_REFRESH_TIME: int = 5
    SYNCDB_TIME: int = 30

    class Config:
        """

        Config is a class used to manage environment configuration settings.

        Attributes:
            env_file (str): The name of the environment file to load.
        """
        env_file = str(Path(__file__).parent.parent / ".env")
        print(env_file)


settings = Settings()

if __name__ == '__main__':
    print(settings.BASE_DIR)
    # print(str(Path(__file__).parent.parent / ".env"))
