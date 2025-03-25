import re


def clean_text(texto):
    # Patrón para caracteres no alfanuméricos
    patron = re.compile(r'\W+', re.UNICODE)

    # Reemplaza los caracteres no alfanuméricos por espacios
    texto_limpio = patron.sub(' ', texto)

    return texto_limpio.strip()