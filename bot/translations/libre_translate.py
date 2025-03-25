#!/usr/bin/env python3
""" libre_translate.py """
import requests

from settings.const import HEADERS


class LibreTranslate:
    """
    A class to perform text translation using the LibreTranslate API.

    This class facilitates the translation of text between various languages
    by interacting with LibreTranslate's API endpoints. It is designed to
    make HTTP POST requests to the LibreTranslate service to translate text
    from a source language to a target language.

    Attributes:
        url (str): The API endpoint for LibreTranslate translation requests.
    """

    def __init__(self):
        self.url = "http://localhost:5000/translate"

    def translate(self, text, source, target):
        """
        Translates text from a source language to a target language using the LibreTranslate API.

        This method sends a POST request to the URL endpoint of the LibreTranslate API, with the
        text to be translated, the source language, and the target language specified. The response
        from the API contains the translated text, while the method also prints the API request URL
        and the raw response content.

        Args:
            text (str): The text to be translated.
            source (str): The source language code of the text (e.g., "en" for English).
            target (str): The target language code for the translation (e.g., "es" for Spanish).

        Returns:
            str: The original text provided as input (no actual transformation occurs in this code).
        """

        payload = {
            "q": text,
            "source": source or "auto",
            "target": target,
            "format": "text",
        }

        response = requests.post(self.url, json=payload, headers=HEADERS)

        if response.status_code == 200:
            # Parse the response and return the translated text
            translated_text = response.json().get("translatedText", "")
            return translated_text
        else:
            # Print the error and return an empty string
            print(f"Error: {response.status_code}, {response.content}")
            return ""


if __name__ == '__main__':
    libre = LibreTranslate()
    print(libre.translate("Hola", "es", "en"))
