from enum import Enum
from dataclasses import dataclass
from typing import Optional, Any, List, TypeVar, Type, cast, Callable
from datetime import datetime
from uuid import UUID
import dateutil.parser

T = TypeVar("T")
EnumT = TypeVar("EnumT", bound=Enum)


# def from_int(x: Any) -> int:
#     assert isinstance(x, int) and not isinstance(x, bool)
#     return x
#
#
# def from_none(x: Any) -> Any:
#     assert x is None
#     return x
#
#
def from_union(fs, x):
    for f in fs:
        try:
            return f(x)
        except:
            pass
    assert False


# def from_str(x: Any) -> str:
#     assert isinstance(x, str)
#     return x
#
#
# def from_datetime(x: Any) -> datetime:
#     return dateutil.parser.parse(x)
#
#
# def to_enum(c: Type[EnumT], x: Any) -> EnumT:
#     assert isinstance(x, c)
#     return x.value
#
#
# def is_type(t: Type[T], x: Any) -> T:
#     assert isinstance(x, t)
#     return x


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]


class Descripcion(Enum):
    AZUAY = "AZUAY"
    CUENCA = "CUENCA"
    NABON = "NABON"
    SIGSIG = "SIGSIG"


class Estado(Enum):
    A = "A"
    C = "C"


@dataclass
class Canton:
    id: Optional[int] = None
    parent_id: Optional[int] = None
    descripcion: Optional[Descripcion] = None
    tipo: Optional[Estado] = None
    codigo: Optional[str] = None
    estado: Optional[Estado] = None
    created: Optional[datetime] = None
    region: Optional[int] = None

    @staticmethod
    def from_dict(obj: Any) -> 'Canton':
        assert isinstance(obj, dict)
        id = obj.get("id")
        parent_id = obj.get("parent_id")
        descripcion = obj.get("descripcion")
        tipo = obj.get("tipo")
        codigo = obj.get("codigo")
        estado = obj.get("estado")
        created = obj.get("created")
        region = obj.get("region")
        return Canton(id, parent_id, descripcion, tipo, codigo, estado, created, region)

    def to_dict(self) -> dict:
        result: dict = {}
        if self.id is not None:
            result["id"] = self.id
        if self.parent_id is not None:
            result["parent_id"] = self.parent_id
        if self.descripcion is not None:
            result["descripcion"] = self.descripcion
        if self.tipo is not None:
            result["tipo"] = self.tipo
        if self.codigo is not None:
            result["codigo"] = self.codigo
        if self.estado is not None:
            result["estado"] = self.estado
        if self.created is not None:
            result["created"] = self.created
        if self.region is not None:
            result["region"] = self.region
        return result


class CentroNombre(Enum):
    ECU_911__CUENCA = "ECU_911_CUENCA"


@dataclass
class Centro:
    id: Optional[int] = None
    nombre: Optional[CentroNombre] = None
    provincia_id: Optional[int] = None

    @staticmethod
    def from_dict(obj: Any) -> 'Centro':
        assert isinstance(obj, dict)
        id = obj.get("id")
        nombre = obj.get("nombre")
        provincia_id = obj.get("provincia_id")
        return Centro(id, nombre, provincia_id)

    def to_dict(self) -> dict:
        result: dict = {}
        if self.id is not None:
            result["id"] = self.id
        if self.nombre is not None:
            result["nombre"] = self.nombre
        if self.provincia_id is not None:
            result["provincia_id"] = self.provincia_id
        return result


@dataclass
class Via:
    id: Optional[UUID] = None
    descripcion: Optional[str] = None
    codigo: None = None
    estado_actual_id: Optional[int] = None
    centro_id: Optional[int] = None
    provincia_id: Optional[int] = None
    canton_id: Optional[int] = None
    observaciones: Optional[str] = None
    created: Optional[datetime] = None
    modified: Optional[datetime] = None
    categoria_id: Optional[int] = None
    estado: Optional[Estado] = None

    @staticmethod
    def from_dict(obj: Any) -> 'Via':
        assert isinstance(obj, dict)
        id = obj.get("id")
        descripcion = obj.get("descripcion")
        codigo = obj.get("codigo")
        estado_actual_id = obj.get("estado_actual_id")
        centro_id = obj.get("centro_id")
        provincia_id = obj.get("provincia_id")
        canton_id = obj.get("canton_id")
        observaciones = obj.get("observaciones")
        created = obj.get("created")
        modified = obj.get("modified")
        categoria_id = obj.get("categoria_id")
        estado = obj.get("estado")
        return Via(id, descripcion, codigo, estado_actual_id, centro_id, provincia_id, canton_id, observaciones,
                   created, modified, categoria_id, estado)

    def to_dict(self) -> dict:
        result: dict = {}
        if self.id is not None:
            result["id"] = self.id
        if self.descripcion is not None:
            result["descripcion"] = self.descripcion
        if self.codigo is not None:
            result["codigo"] = self.codigo
        if self.estado_actual_id is not None:
            result["estado_actual_id"] = self.estado_actual_id
        if self.centro_id is not None:
            result["centro_id"] = self.centro_id
        if self.provincia_id is not None:
            result["provincia_id"] = self.provincia_id
        if self.canton_id is not None:
            result["canton_id"] = self.canton_id
        if self.observaciones is not None:
            result["observaciones"] = self.observaciones
        if self.created is not None:
            result["created"] = self.created
        if self.modified is not None:
            result["modified"] = self.modified
        if self.categoria_id is not None:
            result["categoria_id"] = self.categoria_id
        if self.estado is not None:
            result["estado"] = self.estado
        return result


@dataclass
class ViaAlterna:
    id: Optional[UUID] = None
    via_id: Optional[UUID] = None
    via_alterna_id: Optional[UUID] = None
    created: Optional[datetime] = None
    via: Optional[Via] = None

    @staticmethod
    def from_dict(obj: Any) -> 'ViaAlterna':
        assert isinstance(obj, dict)
        id = obj.get("id")
        via_id = obj.get("via_id")
        via_alterna_id = obj.get("via_alterna_id")
        created = obj.get("created")
        via = obj.get("Via")
        return ViaAlterna(id, via_id, via_alterna_id, created, via)

    def to_dict(self) -> dict:
        result: dict = {}
        if self.id is not None:
            result["id"] = self.id
        if self.via_id is not None:
            result["via_id"] = self.via_id
        if self.via_alterna_id is not None:
            result["via_alterna_id"] = self.via_alterna_id
        if self.created is not None:
            result["created"] = self.created
        if self.via is not None:
            result["Via"] = self.via
        return result


class EstadoActualNombre(Enum):
    ARTERIAL = "ARTERIAL"
    COLECTORA = "COLECTORA"
    HABILITADA = "HABILITADA"
    PARCIALMENTE_HABILITADA = "PARCIALMENTE HABILITADA"


@dataclass
class EstadoActual:
    id: Optional[int] = None
    grupo_id: Optional[int] = None
    parent_id: Optional[int] = None
    nombre: Optional[EstadoActualNombre] = None
    details: Optional[Any] = None
    estado: Optional[Estado] = None
    created: Optional[datetime] = None

    @staticmethod
    def from_dict(obj: Any) -> 'EstadoActual':
        assert isinstance(obj, dict)
        id = obj.get("id")
        grupo_id = obj.get("grupo_id")
        parent_id = obj.get("parent_id")
        nombre = obj.get("nombre")
        details = obj.get("details")
        estado = obj.get("estado")
        created = obj.get("created")
        return EstadoActual(id, grupo_id, parent_id, nombre, details, estado, created)

    def to_dict(self) -> dict:
        result: dict = {}
        if self.id is not None:
            result["id"] = self.id
        if self.grupo_id is not None:
            result["grupo_id"] = self.grupo_id
        if self.parent_id is not None:
            result["parent_id"] = self.parent_id
        if self.nombre is not None:
            result["nombre"] = self.nombre
        if self.details is not None:
            result["details"] = self.details
        if self.estado is not None:
            result["estado"] = self.estado
        if self.created is not None:
            result["created"] = self.created
        return result


@dataclass
class Datum:
    id: Optional[UUID] = None
    codigo: Optional[Any] = None
    descripcion: Optional[str] = None
    estado_actual_id: Optional[int] = None
    centro_id: Optional[int] = None
    provincia_id: Optional[int] = None
    canton_id: Optional[int] = None
    observaciones: Optional[str] = None
    created: Optional[datetime] = None
    modified: Optional[datetime] = None
    categoria_id: Optional[int] = None
    estado: Optional[Estado] = None
    group_detail: Optional[EstadoActual] = list
    estado_actual: Optional[EstadoActual] = list
    centro: Optional[Centro] = None
    provincia: Optional[Canton] = None
    canton: Optional[Canton] = None
    via_alterna: Optional[List[ViaAlterna]] = list
    detalle_via_alterna: Optional[List[ViaAlterna]] = list

    @staticmethod
    def from_dict(obj: Any) -> 'Datum':
        assert isinstance(obj, dict)
        id = obj.get("id")
        descripcion = obj.get("descripcion")
        codigo = obj.get("codigo")
        estado_actual_id = obj.get("estado_actual_id")
        centro_id = obj.get("centro_id")
        provincia_id = obj.get("provincia_id")
        canton_id = obj.get("canton_id")
        observaciones = obj.get("observaciones")
        created = obj.get("created")
        modified = obj.get("modified")
        categoria_id = obj.get("categoria_id")
        estado = obj.get("estado")
        group_detail = obj.get("GroupDetail")
        estado_actual = obj.get("EstadoActual")
        centro = obj.get("Centro")
        provincia = from_union([Canton.from_dict], obj.get("Provincia"))
        canton = obj.get("Canton")
        via_alterna = obj.get("ViaAlterna")
        detalle_via_alterna = obj.get("DetalleViaAlterna")
        return Datum(id, descripcion, codigo, estado_actual_id, centro_id, provincia_id, canton_id, observaciones,
                     created, modified, categoria_id, estado, group_detail, estado_actual, centro, provincia, canton,
                     via_alterna, detalle_via_alterna)

    def to_dict(self) -> dict:
        result: dict = {}
        if self.id is not None:
            result["id"] = self.id
        if self.descripcion is not None:
            result["descripcion"] = self.descripcion
        if self.codigo is not None:
            result["codigo"] = self.codigo
        if self.estado_actual_id is not None:
            result["estado_actual_id"] = self.estado_actual_id
        if self.centro_id is not None:
            result["centro_id"] = self.centro_id
        if self.provincia_id is not None:
            result["provincia_id"] = self.provincia_id
        if self.canton_id is not None:
            result["canton_id"] = self.canton_id
        if self.observaciones is not None:
            result["observaciones"] = self.observaciones
        if self.created is not None:
            result["created"] = self.created
        if self.modified is not None:
            result["modified"] = self.modified
        if self.categoria_id is not None:
            result["categoria_id"] = self.categoria_id
        if self.estado is not None:
            result["estado"] = self.estado
        if self.group_detail is not None:
            result["GroupDetail"] = self.group_detail
        if self.estado_actual is not None:
            result["EstadoActual"] = self.estado_actual
        if self.centro is not None:
            result["Centro"] = self.centro
        if self.provincia is not None:
            result["Provincia"] = self.provincia
        if self.canton is not None:
            result["Canton"] = self.canton
        if self.via_alterna is not None:
            result["ViaAlterna"] = self.via_alterna
        if self.detalle_via_alterna is not None:
            result["DetalleViaAlterna"] = self.detalle_via_alterna
        return result


@dataclass
class ViasEC:
    data: Optional[List[Datum]] = None
    total: Optional[int] = None
    code: Optional[int] = None

    @staticmethod
    def from_dict(obj: Any) -> 'ViasEC':
        assert isinstance(obj, dict)
        data = obj.get("data")
        total = obj.get("total")
        code = obj.get("code")
        return ViasEC(data, total, code)

    def to_dict(self) -> dict:
        result: dict = {}
        if self.data is not None:
            result["data"] = self.data
        if self.total is not None:
            result["total"] = self.total
        if self.code is not None:
            result["code"] = self.code
        return result


def vias_ec_from_dict(s: Any) -> ViasEC:
    return ViasEC.from_dict(s)


def vias_ec_to_dict(x: ViasEC) -> Any:
    return to_class(ViasEC, x)
