# import io
import io
import logging
import os
import pickle
import sqlite3
from datetime import datetime, timedelta
from time import time

import pandas as pd

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chromium.options import ChromiumOptions
from selenium.webdriver.common.by import By

from src.settings import settings

logger = logging.getLogger(__name__)


class ViasEcuadorScraper:
    """
    WebScraper

    This class represents a web scraper that fetches data from a webpage and performs necessary operations on the data.

    Attributes:
        url (str): The URL of the webpage to scrape.
        options: The options to configure the WebDriver.
        driver: The WebDriver instance for interacting with the webpage.
        db_path (str): The path to the SQLite database.

    Methods:
        __init__(self)
            Initializes an instance of the class.

        fetch_table_data(self)
            Fetches table data from a webpage and performs necessary operations on the data.

        save_to_database(self, dataframe)
            Save the given dataframe to the database.

        clean_old_data(self)
            Deletes data from the database that is older than a certain number of days.

        close_driver(self)
            Closes the WebDriver instance.

    """

    def __init__(self):
        """Initializes an instance of the class.

        This method sets up the necessary variables and configurations for the class instance.

        Parameters:
        - self: the instance of the class.

        Returns:
        None
        """
        self.url = settings.URL_SCRAPPING_WEB

        self.cache_file = settings.CACHE_FILE
        self.cache_ttl = settings.CACHE_TIME_EXPIRATION

        self.options = Options()
        self.options.add_argument('--headless')  # Asegura que se ejecute en modo sin cabeza
        self.options.add_argument('--disable-gpu')  # Por compatibilidad, en entornos Linux
        self.options.add_argument('--no-sandbox')  # Importante para entornos Docker
        self.options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Remote(options=self.options)

        self.db_path = settings.DATABASE_URL

    def _is_cache_valid(self):
        """
        Verifica si el cache es válido (si existe y no está expirado).
        """
        if os.path.exists(self.cache_file):
            # Verificar si el cache está dentro del tiempo permitido
            cache_age = time() - os.path.getmtime(self.cache_file)
            return cache_age < self.cache_ttl
        return False

    def _load_cache(self):
        """
        Carga el cache desde el archivo.
        """
        with open(self.cache_file, "rb") as file:
            return pickle.load(file)

    def _save_cache(self, data):
        """
        Guarda el contenido de Selenium en un archivo de cache.
        """
        with open(self.cache_file, "wb") as file:
            pickle.dump(data, file)

    def _selenium_cache(self):
        """
        Maneja el cache de la solicitud Selenium.
        """
        # Si el cache es válido, cargarlo
        if self._is_cache_valid():
            print("Cargando datos desde el cache.")
            return self._load_cache()

        # Si no hay cache válido, usar Selenium para obtener los datos
        print("Realizando nueva solicitud con Selenium.")
        self.driver.get(self.url)
        self.driver.implicitly_wait(10)

        # Guardar el HTML de la página en el cache
        page_source = self.driver.page_source
        self._save_cache(page_source)

        return page_source

    def get_states_vias(self):
        """
        Fetches table data from a webpage and performs necessary operations on the data.

        Returns:
            None
        """
        try:
            # Obtener la página desde el cache o mediante Selenium
            response = self._selenium_cache()

            # Si se carga desde el cache, procesar el HTML directamente
            if isinstance(response, str):  # Cuando `response` es el HTML de la página
                print("Procesando datos desde el cache.")
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response, "html.parser")

                # Extraer la fecha desde el HTML cacheado
                date_consult = soup.find(id="fecha")
                if date_consult:
                    datetime_consult = datetime.strptime(date_consult.text, "%d/%m/%Y, %H:%M:%S")
                else:
                    datetime_consult = None

                # Extraer las tablas desde el HTML cacheado
                tables = soup.find("table")
                if tables:
                    table = pd.read_html(io.StringIO(str(tables)))[0]
                else:
                    table = None

            # Si se hace una nueva solicitud con Selenium, procesar los elementos normalmente
            else:
                print("Procesando datos con Selenium.")
                date_consult = self.driver.find_element(By.ID, "fecha")
                if date_consult.text:
                    datetime_consult = datetime.strptime(date_consult.text, "%d/%m/%Y, %H:%M:%S")
                else:
                    datetime_consult = None

                tables = self.driver.find_element(By.TAG_NAME, "table")
                if tables:
                    table = pd.read_html(io.StringIO(tables.get_attribute('outerHTML')))[0]
                else:
                    table = None

        except Exception as e:
            print(f"Ocurrió un error en el servidor Selenium: {e}")
            return

        # Guardar los datos en la base de datos
        try:
            self.save_to_database(table, datetime_consult)
        except Exception as db_error:
            print(f"Error al guardar en la base de datos: {db_error}")
        finally:
            # Si se usó Selenium, asegurarse de cerrar el driver
            if not isinstance(response, str):  # Si no se cargó desde el cache
                self.driver.quit()

    # def get_states_vias(self):
    #     """
    #     Fetches table data from a webpage and performs necessary operations on the data.
    #
    #     Returns:
    #         None
    #
    #     Parameters:
    #         self (Object): The current instance of the class.
    #
    #     Usage:
    #         To fetch table data, use the fetch_table_data() method.
    #     """
    #     try:
    #         # self.driver.get(self.url)
    #         # self.driver.implicitly_wait(10)
    #         response = self._selenium_cache()
    #
    #         print(response.get_cache())
    #
    #         date_consult = self.driver.find_element(By.ID, "fecha")
    #         if date_consult.text:
    #             datetime_consult = datetime.strptime(date_consult.text, "%d/%m/%Y, %H:%M:%S")
    #         else:
    #             datetime_consult = None
    #
    #         tables = self.driver.find_element(By.TAG_NAME, "table")
    #         if tables:
    #             table = pd.read_html(io.StringIO(tables.get_attribute('outerHTML')))
    #         else:
    #             table = None
    #     except Exception as e:
    #         print(f"Ocurrió un error en el servidor Selenium: {e}")
    #     else:
    #         self.save_to_database(table, datetime_consult)
    #     finally:
    #         self.driver.quit()

    def save_to_database(self, dataframe):
        """
        Save the given dataframe to the database.

        :param dataframe: The dataframe to save.
        """
        print(self.db_path)
        connection = sqlite3.connect(self.db_path)
        dataframe.to_sql('vias_ec', connection, if_exists='append', index=False)
        connection.close()

    def clean_old_data(self):
        """

        Clean_old_data method deletes data from vias_ec table in the database that is older than 7 days.

        Parameters:
            self (object): The instance of the class calling the method.

        Returns:
            None

        """
        print(self.db_path)
        connection = sqlite3.connect(self.db_path)

        # Obtener la fecha actual y la fecha de hace 7 días
        seven_days_ago = datetime.now() - timedelta(days=settings.DAYS_TO_KEEP_DATA)

        # Eliminar datos mayores a 7 días
        connection.execute(
            f"DELETE FROM vias_ec "
            f"WHERE fecha_hora_extraccion < '{seven_days_ago.strftime('%Y-%m-%d')}'"
        )

        connection.close()

    def close_driver(self):
        """
        Close the driver.

        This method closes the driver instance.

        Parameters:
            self: The instance of the object.

        Returns:
            None
        """
        self.driver.close()


if __name__ == '__main__':
    scraper = ViasEcuadorScraper()
    scraper.get_states_vias()
