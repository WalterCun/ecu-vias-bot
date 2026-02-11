import logging

import requests
from requests.adapters import HTTPAdapter
from requests_cache import CachedSession
from urllib3.util.retry import Retry

from bot.settings import settings
from bot.settings.const import HEADERS

logger = logging.getLogger(__name__)


class ViasEcuadorAPI:
    session = CachedSession(
        cache_name=settings.BASE_DIR / settings.CACHE_NAME,
        backend='sqlite',
        expire_after=settings.CACHE_TIME_EXPIRATION
    )

    def __init__(self):
        self.url = settings.URL_SCRAPPING_WEB

        retry = Retry(
            total=3,
            read=3,
            connect=3,
            backoff_factor=0.8,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)

    def get_states_vias(self):
        try:
            response = self.session.get(
                self.url,
                headers=HEADERS,
                timeout=15,
            )
            response.raise_for_status()
            vias = response.json()
        except requests.RequestException as exc:
            logger.error("Error consultando API de vías: %s", exc)
            return []
        except ValueError as exc:
            logger.error("Respuesta JSON inválida de API de vías: %s", exc)
            return []

        data = vias.get('data', []) if isinstance(vias, dict) else []
        return data if isinstance(data, list) else []
