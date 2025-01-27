import io
import sqlite3
from datetime import datetime, timedelta

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from src.config.settings import URL, DB_PATH, DAYS_TO_KEEP_DATA


class WebScraper:
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
        self.url = URL
        try:
            # Ejecutar de forma local
            self.options = Options()
            self.options.add_argument("--headless")
            self.driver = webdriver.Chrome(options=self.options)
        except Exception as e:
            # Ejecutar de forma Dockenizada
            self.options = webdriver.ChromeOptions()
            self.driver = webdriver.Remote(options=self.options)
        self.db_path = DB_PATH

    def fetch_table_data(self):
        """
        Fetches table data from a webpage and performs necessary operations on the data.

        Returns:
            None

        Parameters:
            self (Object): The current instance of the class.

        Usage:
            To fetch table data, use the fetch_table_data() method.
        """
        self.driver.get(self.url)
        div = self.driver.find_element(By.ID, 'tableVias')
        table = div.find_element(By.TAG_NAME, 'table')
        dataframes = pd.read_html(io.StringIO(table.get_attribute('outerHTML')))
        df = dataframes[0]

        # Agregar columna 'fecha_hora_extraccion'
        df['fecha_hora_extraccion'] = datetime.now()

        # Guardar los datos en la base de datos local
        self.save_to_database(df)
        self.clean_old_data()

    def save_to_database(self, dataframe):
        """
        Save the given dataframe to the database.

        :param dataframe: The dataframe to save.
        """
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
        connection = sqlite3.connect(self.db_path)

        # Obtener la fecha actual y la fecha de hace 7 días
        seven_days_ago = datetime.now() - timedelta(days=DAYS_TO_KEEP_DATA)

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


def vias_load_db():
    """
    Loads database with table data from web.

    Returns:
        None
    """
    scraper = WebScraper()
    scraper.fetch_table_data()
    scraper.clean_old_data()
    scraper.close_driver()


if __name__ == '__main__':
    vias_load_db()
    print("Finalizado")
