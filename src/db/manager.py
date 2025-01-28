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
import json
import logging
from datetime import datetime

from tortoise import Tortoise

from src.settings import settings

# from config import settings
# from db.models import Posts, PostsDetails, PostImages
# from db.models.user_model import Config
# from db.seeders.user_seed import seed_data
# from scrapers import SkokkaScraper
# from tools import URL
# from tools.fomats import fjson
# from tools.parse import parse_price
# from tools.urls import clean_url

logger = logging.getLogger(__name__)

DATABASE_CONFIG = {
    "connections": {
        # "default": "sqlite://test.db"  # Cambia a PostgreSQL/MySQL si lo necesitas
        "default": f'sqlite://{settings.BASE_DIR / settings.DB_NAME}' if settings.DB_TYPE == 'sqlite' else settings.DB_URL
    },
    "apps": {
        "models": {
            # "models": ["post_model", "aerich.models"],  # Tu archivo de modelo
            "models": ['db.models', 'aerich.models'],  # Tu archivo de modelo
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


# async def sync_db():
#     """
#     Continuously synchronizes the database by checking for outdated records and performing cleanup actions at regular intervals.
#
#     The function periodically checks the current time and performs a cleanup process to remove database records older than a specific
#     threshold, ensuring the database remains up-to-date. It also logs the operation's progress for monitoring purposes. The function
#     runs indefinitely, pausing between iterations for a configurable time interval.
#
#     Raises:
#         None
#     """
#     await init()
#
#     while True:
#         now = datetime.now().date()
#         logger.warning(f">> Revisando la base de datos... {now}")
#         skokka = SkokkaScraper()
#         logger.warning(f'Actualizando informacion de base de datos...')
#         results = await Config.all().distinct().values_list("country", "city", "url")
#         for country, city, url in results:
#             posts = skokka.get_posts(direct_url=url)
#             for post in posts['post']:
#                 post_new = await Posts.all().filter(
#                     country=country,
#                     city=city,
#                     title=post.get('title'),
#                     url=clean_url(post.get('url')),
#                 ).first()
#                 if not post_new:
#                     post_new = await Posts.create(
#                         created_at=datetime.today(),
#                         country=country,
#                         city=city,
#                         title=post.get('title'),
#                         super_top=post.get('super_top'),
#                         url=clean_url(post.get('url')),
#                         content=post.get('content'),
#                         image_url=clean_url(post.get('images', {}).get('sources', [{}])[0].get('src')),
#                         image_description=post.get('images', {}).get('sources', [{}])[0].get('description'),
#                         extras=post.get('extra'),
#                     )
#                     logger.warning(f"Post creado: {post_new}")
#                 else:
#                     logger.warning(f"Post encontrado: {post_new}")
#                 response_post_details = skokka.get_details(URL(post_new.url))
#                 # Agregar detalles al post
#                 post_details_new = await PostsDetails.filter(
#                     id=response_post_details.get('id'),
#                 ).first()
#                 if not post_details_new:
#                     logger.warning(f"Agregando Detalles de Post: {post_new}")
#
#                     post_details_new = await PostsDetails.create(
#                         id=response_post_details.get('id'),
#                         post=post_new,
#                         age=25,  # TODO agregar la edad publicada
#                         whatsapp=response_post_details.get('contact', {}).get('whatsapp'),
#                         cellphone=response_post_details.get('contact', {}).get('cellphone'),
#                         top=not bool(response_post_details.get('super_top')),
#                         super_top=bool(response_post_details.get('super_top')),
#                         about_me=response_post_details.get('about_me'),
#                         about_me_tags=response_post_details.get('about_me_tags', []),
#                         price=parse_price(response_post_details.get('price', 0.0)),
#                         services=response_post_details.get('servicios', []),
#                         who_do_you_serve=response_post_details.get('who_do_you_serve', []),
#                         meeting_place=response_post_details.get('meeting_place', []),
#                         payments=response_post_details.get('sistemas de pago', []),
#                     )
#                     logger.warning(f"Detalles del post creados: {post_details_new}")
#                     for i, photo in enumerate(json.loads(fjson(response_post_details.get('photos', '[]')))):
#                         # Agregar imágenes al detalle del post
#                         await PostImages.create(
#                             post=post_details_new,
#                             image_url=photo,
#                             is_main=True if i == 0 else False,
#                             caption=response_post_details.get('caption', 'Imagen principal del anuncio')
#                         )
#         # Eliminar registros más antiguos de 1 día
#         logger.warning(f">> Eliminando registros antiguos...")
#         # delete_post_images = await PostImages.filter(created_at__lt=now - timedelta(days=settings.SYNCDB_DELETE_DAYS))
#         # logger.info(f"Imagenes eliminadas: {len(delete_post_images)}")
#         # await delete_post_images.delete()
#
#         # delete_post_details = await PostsDetails.filter(
#         #     created_at__lt=now - timedelta(days=settings.SYNCDB_DELETE_DAYS))
#         # logger.info(f"Detalles eliminados: {len(delete_post_details)}")
#         # await delete_post_images.delete()
#         delete_post = await Posts.filter(created_at__lt=now)
#         print(now)
#         print(delete_post)
#         # delete_post = await Posts.filter(created_at__lt=now - timedelta(days=settings.SYNCDB_DELETE_DAYS))
#         logger.warning(f"Posts eliminados: {len(delete_post)}")
#         # await delete_post.delete()
#
#         logger.warning(f">> Base de datos actualizada: ")
#         await asyncio.sleep(settings.SYNCDB_TIME)  # Ejecutar cada hora


if __name__ == '__main__':
    async def test_models():
        await init()

        # user = await UserConfig.create(id=1995, name='Walter Cun')
        # print("User created successfully.", user)

        # Leer registros
        # registros = await UserConfig.all()
        # logger.info("Todos los registros:", registros)
    #
    #     user = await UserConfig.get(id=1995)
    #     logger.info("Usuario:", user.name)
    #
    #     await close_db()
    #
    #
    # asyncio.run(test_models())

    # asyncio.run(sync_db())
