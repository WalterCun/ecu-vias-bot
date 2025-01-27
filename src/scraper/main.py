import re
from datetime import datetime
from time import sleep

from src.scraper.web_scraper import vias_load_db


def load_data() -> None:
    """
        Función para cargar datos, sincronizando la ejecución cada hora en punto.

        Utiliza una expresión regular para verificar si la hora actual
        termina en ":00:00" o ":00:MM". Muestra mensajes de búsqueda
        y sincronización para proporcionar información al usuario.

        Returns:
            None
        """
    synchronize = False
    time_pattern = re.compile(r"\b(\d{2}):00:(\d{2})\b")

    while True:
        current_time = datetime.now()  # + timedelta(minutes=15)
        current_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

        if not time_pattern.search(current_time) and not synchronize:
            print(f"Search Synchronize: {current_time}")
        elif time_pattern.search(current_time) and not synchronize:
            print(f"Synchronize: {current_time}")
            vias_load_db()
            synchronize = True
        else:
            print(f"Recolectando Datos -> {current_time}")
            vias_load_db()

        # Espera 1 segundo si no está sincronizado, o espera hasta la próxima hora en punto si está sincronizado
        sleep((60 * 60) if synchronize else 1)
