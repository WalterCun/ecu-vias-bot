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
import logging
from datetime import datetime, timedelta
from time import sleep

import pytz

from bot.db.models import Vias
from bot.services.api import ViasEcuadorAPI
from bot.settings import settings

from colorama import Fore, init

init(autoreset=True)

logger = logging.getLogger(__name__)


# async def init():
#     """
#     Initializes the Tortoise ORM and generates database schemas asynchronously.
#
#     This function sets up the ORM by initializing it with the provided database configuration
#     and then generates the necessary schemas for the database according to the defined models.
#
#     Raises:
#         ConfigurationError: If the provided database configuration is invalid.
#         OperationalError: If there is an issue connecting to the database.
#     """
#     await Tortoise.init(config=DATABASE_CONFIG)
#     await Tortoise.generate_schemas()
#
#
# async def close_db():
#     """
#     Closes all database connections managed by Tortoise ORM.
#
#     This asynchronous function ensures that all active database connections are
#     properly closed. It is used to clean up resources when the application shuts
#     down or when database connections need to be explicitly terminated.
#
#     Raises:
#         TortoiseException: If there is an issue during connection closure.
#     """
#     await Tortoise.close_connections()


async def sync_db():
    """
    Continuously synchronizes the database by checking for outdated records and performing cleanup actions at regular intervals.

    The function periodically checks the current time and performs a cleanup process to remove database records older than a specific
    threshold, ensuring the database remains up-to-date. It also logs the operation's progress for monitoring purposes. The function
    runs indefinitely, pausing between iterations for a configurable time interval.

    Raises:
        None
    """
    # Definir la zona horaria de Ecuador
    ecuador_tz = pytz.timezone('America/Guayaquil')

    logger.info('Obtener hora por default cuando la base esta vacia')
    ahora = datetime.now(ecuador_tz)
    # ahora = datetime.now(ecuador_tz)
    last_request = await Vias.filter().order_by("-extraction_datetime").first()
    last_request = last_request.extraction_datetime_ec if last_request else datetime(ahora.year, ahora.month, 1)

    if last_request:
        last_request = last_request.astimezone(ecuador_tz)  # Asegurar que sea aware y en UTC
    else:
        last_request = datetime(ahora.year, ahora.month, 1, tzinfo=ecuador_tz)

    logger.info('Crear instancias de ViasEcuadorScraper ')
    api = ViasEcuadorAPI()

    while True:
        now = datetime.now(ecuador_tz)
        logger.warning(Fore.BLUE + f">> Revisando la base de datos... {now}")

        logger.warning(
            Fore.WHITE + f'last_request: {now - last_request} > {settings.SYNCDB_TIME} : {(now - last_request) > timedelta(seconds=settings.SYNCDB_TIME)}')

        if (now - last_request) > timedelta(seconds=settings.SYNCDB_TIME):
            data = api.get_states_vias()
            for row in data:

                via = await Vias.filter(province=row.get('Provincia', {}).get('descripcion'),
                                        via=row.get('descripcion')).first()

                if via is not None and (
                        via.state != row.get('EstadoActual', {}).get('nombre') or via.observations != row.get(
                    'observaciones')):
                    logger.warning(Fore.GREEN + 'Registro Encontrado, proceder a actualizar informacion')
                    await Vias.filter(id=via.id).update(
                        state=row.get('EstadoActual', {}).get('nombre'),
                        observations=row.get('observaciones'),
                        alternate_via=row.get('DetalleViaAlterna')[0].get('Via', {}).get('descripcion') if row.get(
                            'DetalleViaAlterna') else None,
                        extraction_datetime=now,
                    )
                elif via is not None and (
                        via.state == row.get('EstadoActual', {}).get('nombre') or via.observations == row.get(
                    'observaciones')):
                    logger.warning(Fore.BLUE + f'No hay cambios.....')
                    continue
                else:
                    logger.warning(Fore.RED + f'Ingresando registro: {via}')
                    await Vias.create(
                        province=row.get('Provincia', {}).get('descripcion'),
                        via=row.get('descripcion'),
                        state=row.get('EstadoActual', {}).get('nombre'),
                        observations=row.get('observaciones'),
                        alternate_via=row.get('DetalleViaAlterna')[0].get('Via', {}).get('descripcion') if row.get(
                            'DetalleViaAlterna') else None,
                    )

            last_request = now

        logger.warning(Fore.BLUE + f">> Base de datos actualizada: ")
        sleep(settings.SYNCDB_REFRESH_TIME)

# if __name__ == '__main__':
#     asyncio.run(sync_db())
