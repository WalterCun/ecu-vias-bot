# from datetime import time
#
# from src.controller.languages.translations import language

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/108.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Content-Type": "application/json"
}

# ONCE_A_DAY: dict[str, time] = {
#     f"{hour % 12 or 12} {'AM' if hour < 12 else 'PM'}": time(hour=hour) for hour in range(24)
# }
#
# from bot.translations.core import translate

# SEVERAL_TIMES_A_DAY: list = [
#     translate.times_one_hour,
#     translate.times_three_hour,
#     translate.times_six_hour
# ]

PROVINCES: list[str] = [
    'Azuay', 'Bolivar', 'Cañar', 'Carchi', 'Chimborazo', 'Cotopaxi', 'El Oro', 'Esmeraldas', 'Galápagos', 'Guayaquil',
    'Imbabura', 'Loja', 'Los Ríos', 'Manabí', 'Morona Santiago', 'Napo', 'Sucumbíos', 'Pastaza', 'Pinchincha',
    'Santa Elena', 'Santo Domingo de los Tsáchilas', 'Francisco de Orellana', 'Tungurahua', 'Zamora Chinchipe'
]
