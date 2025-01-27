"""src/config/settings.py"""

from pathlib import Path

from pydantic_settings import BaseSettings

from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.


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
    BASE_DIR: Path = Path(__file__).parent.parent.parent
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

    DATABASE_URL: str = 'postgres://localhost:5432/ecuvias'
    REDIS_URL: str = 'redis://localhost:6379/0'

    # Bot Telegram
    TELEGRAM_KEY_BOT: str
    ID_ADMIN: int

    # Web Scrapping
    URL_SCRAPPING_WEB: str
    DAYS_TO_KEEP_DATA: str

    class Config:
        """

        Config is a class used to manage environment configuration settings.

        Attributes:
            env_file (str): The name of the environment file to load.
        """
        env_file = ".env"


settings = Settings()

if __name__ == '__main__':
    print(settings.BASE_DIR
          )
