"""
This file manages interactions with a database using Tortoise ORM and provides functions 
to initialize, close, and synchronize the database models and connections.

Key functionalities include:
- Initialization of the Tortoise ORM with database configuration.
- Periodic database synchronization and cleanup processes.
- Example usage of database models for testing and debugging.

Modules Imported:
- asyncio: For running asynchronous operations.
- logging: To log application messages.
- datetime: To handle date and time operations.
- time: For introducing delays.
- tortoise: To interact with the database as an ORM.

Note:
Update the `DATABASE_CONFIG` dictionary as needed to reflect the appropriate settings 
for your database type and connection details.

"""
import asyncio
import logging
from datetime import datetime, timedelta

from tortoise import Tortoise

from src.db.models import Vias
from src.scraper.web_scraper import ViasEcuadorScraper
from src.settings import settings

logger = logging.getLogger(__name__)

DATABASE_CONFIG = {
    "connections": {
        # "default": "sqlite://test.db"  # Cambia a PostgreSQL/MySQL si lo necesitas
        # "default": f'sqlite://{settings.BASE_DIR / settings.DB_NAME}'
        "default": settings.DATABASE_URL
    },
    "apps": {
        "models": {
            # "models": ["post_model", "aerich.models"],  # Tu archivo de modelo
            "models": ['src.db.models'],  # Tu archivo de modelo
            "default_connection": "default",
        }
    },
}


async def init():
    """
    Initializes the Tortoise ORM and generates database schemas asynchronously.

    This function sets up the ORM by initializing it with the provided database configuration
    and then generates the necessary schemas for the database according to the defined models.

    Raises:
        ConfigurationError: If the provided database configuration is invalid.
        OperationalError: If there is an issue connecting to the database.
    """
    await Tortoise.init(config=DATABASE_CONFIG)
    await Tortoise.generate_schemas()


async def close_db():
    """
    Closes all database connections managed by Tortoise ORM.

    This asynchronous function ensures that all active database connections are
    properly closed. It is used to clean up resources when the application shuts
    down or when database connections need to be explicitly terminated.

    Raises:
        TortoiseException: If there is an issue during connection closure.
    """
    await Tortoise.close_connections()


async def sync_db():
    """
    Continuously synchronizes the database by checking for outdated records and performing cleanup actions at regular intervals.

    The function periodically checks the current time and performs a cleanup process to remove database records older than a specific
    threshold, ensuring the database remains up-to-date. It also logs the operation's progress for monitoring purposes. The function
    runs indefinitely, pausing between iterations for a configurable time interval.

    Raises:
        None
    """
    logger.info('Inicializar base de datos')
    await init()

    logger.info('Obtener hora por default cuando la base esta vacia')
    ahora = datetime.now()
    last_request = await Vias.filter().order_by("-extraction_datetime").first()
    last_request = last_request.extraction_datetime if last_request else datetime(ahora.year, ahora.month, 1)

    logger.info('Crear instancias de ViasEcuadorScraper ')
    scraper = ViasEcuadorScraper()

    while True:
        now = datetime.now().date()
        logger.warning(f">> Revisando la base de datos... {now}")

        logger.info(f'last_request: {now - last_request} > {settings.SYNCDB_TIME} : {(now - last_request) > timedelta(seconds=settings.SYNCDB_TIME)}')
        if (now - last_request) > timedelta(seconds=settings.SYNCDB_TIME):
            consult, data = scraper.get_states_vias()

            data = data.to_dict('records')
            print(data)
            #
            # if consult or data:
            #     await Vias.create(
            #         province=
            #         via =
            #     state =
            #     observations =
            #     alternate_via =
            #
            #     page_datetime
            #     )





            last_request = now

            logger.warning(f">> Base de datos actualizada: ")
            await asyncio.sleep(settings.SYNCDB_REFRESH_TIME)

if __name__ == '__main__':
    asyncio.run(sync_db())
