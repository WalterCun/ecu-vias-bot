from requests_cache import CachedSession

from services.structs.viasec import vias_ec_to_dict, vias_ec_from_dict
from settings import settings
from settings.const import HEADERS


class ViasEcuadorAPI:
    session = CachedSession(
        cache_name=settings.BASE_DIR / 'ecuavias.db',
        backend='sqlite',
        expire_after=settings.CACHE_TIME_EXPIRATION
    )

    def __init__(self):
        self.url = 'https://ecu911.gob.ec/Services/WSVias/ViasWeb.php?estado=A&and:%3C%3E:EstadoActual-id=593&order=Provincia-descripcion&limit=200&start=0'
        # self.url = 'https://ecu911.gob.ec/Services/WSVias/ViasWeb.php?estado=A&order=Provincia-descripcion'

    def get_states_vias(self):
        # TODO revisar el estado de validacion con certificado
        cert = str(settings.BASE_DIR / 'services/cerf' / '_.ecu911.gob.ec.crt')
        session = self.session.get(self.url, headers=HEADERS, verify=False)
        # vias = vias_ec_from_dict(session.json())
        vias = session.json()
        if vias.get('code') == 200:
            return vias.get('data')

        return None


if __name__ == '__main__':
    api = ViasEcuadorAPI()
    print(api.get_states_vias())
