""" src/bot_controller/languages/translations.py """
import yaml

from src.settings.config import settings


# class Translator:
#
#     def __init__(self):
#         self.translations = None
#         self.load_translations()
#
#     def load_translations(self, language_code='es'):
#         # Carga las traducciones desde el archivo correspondiente al idioma
#         translation_file = settings.LOCALES_PATH / f"{language_code}.yaml"
#         with open(translation_file, 'r', encoding='utf-8') as file:
#             self.translations = yaml.safe_load(file)
#         self._generate_attributes(self.translations)
#
#     def _generate_attributes(self, data_dict, prefix=''):
#         for key, value in data_dict.items():
#             if isinstance(value, dict):
#                 # Llamada recursiva si el valor actual es un diccionario
#                 self._generate_attributes(value, f'{prefix}{key}_')
#                 # self._generate_attributes(clean_text(value), f'{prefix}{key}_')
#             else:
#                 setattr(self, f'{prefix}{key}', value)
#                 # setattr(self, f'{prefix}{key}', clean_text(value))


class Translator:

    def __init__(self, language_code='es'):
        self.translations = {}
        self.load_translations(language_code)

    def load_translations(self, language_code='es'):
        """
        Carga las traducciones desde un archivo YAML correspondiente al idioma.
        """
        translation_file = settings.LOCALES_PATH / f"{language_code}.yaml"
        try:
            with open(translation_file, 'r', encoding='utf-8') as file:
                self.translations = yaml.safe_load(file) or {}
            self._generate_attributes(self.translations)
        except FileNotFoundError:
            raise FileNotFoundError(f"No se encontró el archivo de traducción: {translation_file}")
        except Exception as e:
            raise RuntimeError(f"Error al cargar las traducciones: {e}")

    def _generate_attributes(self, data, prefix=''):
        """
        Genera atributos dinámicos en la instancia, basados en las claves del diccionario de traducciones.
        """
        for key, value in data.items():
            attr_name = f"{prefix}{key}"
            if isinstance(value, dict):
                # Recursivamente genera atributos para claves anidadas
                self._generate_attributes(value, f"{attr_name}_")
            else:
                setattr(self, attr_name, value)


language = Translator()

# if __name__ == '__main__':
#     t = Translator()
#     t.load_translations()
#     print(t.menu_buttons_cancel)
