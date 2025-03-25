#!/usr/bin/env python3
""" cli.py """
import argparse
import logging

from core import Translator

logger = logging.getLogger(__name__)

def main():
    # Crear el parser de argumentos
    parser = argparse.ArgumentParser(
        description="Herramienta CLI para manejar traducciones"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcomando para agregar texto
    add_parser = subparsers.add_parser("add", help="Agregar una nueva traducción")
    add_parser.add_argument("value", help="El texto traducido")
    add_parser.add_argument("--key", required=True, help="La clave de la traducción")
    add_parser.add_argument("--lang", help="El idioma (e.g., es, en, fr)", default="es")

    auto_translate_parser = subparsers.add_parser('auto_translator', help='Auto translate')
    auto_translate_parser.add_argument('--base', required=True, help='The key of the translation')
    auto_translate_parser.add_argument('--langs', required=True, help='The language (e.g., es, en, fr)', nargs='*',
                                       default='es')
    auto_translate_parser.add_argument('--force', help='Forzar traducciones', action='store_true')

    # Parsear los argumentos de la línea de comandos
    args = parser.parse_args()
    # Procesar comandos
    if args.command == "add":
        handle_add_text(args)
    elif args.command == "auto_translator":
        handle_auto_translate(args)


def handle_add_text(args):
    """
    Maneja el comando 'add_text' para agregar traducciones.
    """
    translator = Translator()
    translator.add_trans(key=args.key, lang=args.lang, value=args.value)
    print(
        f"Traducción agregada: {args.key} -> {args.value} en {args.lang}."
    )


def handle_auto_translate(args):
    """
    Automatically handles the translation of a base language into multiple target languages
    based on the provided arguments.

    Args:
        args: Command-line arguments object containing the following attributes:
            base (str): The base language to translate from.
            langs (Union[str, List[str]]): Target languages to translate into. If 'all' is
                provided, translates into all available languages.
            force (bool): Indicates whether to overwrite existing translations.
    """
    translator = Translator()
    translator.auto_translate(base=args.base, langs='all' if 'all' in args.langs else args.langs, force=args.force)
    print(
        f"Traducciones de {args.base} auto traducidas."
    )


if __name__ == "__main__":
    main()
