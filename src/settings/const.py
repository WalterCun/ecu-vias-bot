from datetime import time

from src.controller.languages.translations import language

ONCE_A_DAY: dict[str, time] = {
    f"{hour % 12 or 12} {'AM' if hour < 12 else 'PM'}": time(hour=hour) for hour in range(24)
}

SEVERAL_TIMES_A_DAY = [
    language.times_one_hour,
    language.times_three_hour,
    language.times_six_hour
]

PROVINCES = ['Azuay', 'Bolivar', 'Cañar', 'Carchi', 'Chimborazo', 'Cotopaxi', 'El Oro', 'Esmeraldas', 'Galápagos',
             'Guayanas', 'Imbabura', 'Loja', 'Los Ríos', 'Manabí', 'Morona Santiago', 'Napo', 'Sucumbíos',
             'Pastaza', 'Pinchincha', 'Santa Elena', 'Santo Domingo de los Tsáchilas', 'Francisco de Orellana',
             'Tungurahua', 'Zamora Chinchipe']
