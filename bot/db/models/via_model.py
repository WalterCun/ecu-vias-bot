from enum import Enum

from pytz import timezone
from tortoise import fields
from tortoise.fields import TextField, CharField
from tortoise.models import Model

ecuador_tz = timezone("America/Guayaquil")  # Definir la zona horaria de Ecuador

class Provincia(Model):
    id = fields.IntField(pk=True)
    descripcion = fields.CharField(max_length=100)
    codigo = fields.CharField(max_length=10, null=True)
    region = fields.CharField(max_length=10, null=True)

    class Meta:
        table = "provincias"

class Canton(Model):
    id = fields.IntField(pk=True)
    descripcion = fields.CharField(max_length=100)

    provincia = fields.ForeignKeyField(
        "models.Provincia",
        related_name="cantones"
    )

    class Meta:
        table = "cantones"

class Centro(Model):
    id = fields.IntField(pk=True)
    nombre = fields.CharField(max_length=100)

    provincia = fields.ForeignKeyField(
        "models.Provincia",
        related_name="centros"
    )

    class Meta:
        table = "centros"

class EstadoActual(Model):
    id = fields.IntField(pk=True)
    nombre = fields.CharField(max_length=50)

    class Meta:
        table = "estado_actual"

class CategoriaVia(Model):
    id = fields.IntField(pk=True)
    nombre = fields.CharField(max_length=50)

    class Meta:
        table = "categoria_via"


# class Vias(Model):
#     """
#     Modelo Tortoise que representa una fila de "vias_ec".
#     """
#     id = fields.IntField(pk=True,auto_increment=True)
#     province = CharField(max_length=50)
#     via = fields.CharField(max_length=100)
#     state = CharField(max_length=50)
#     observations = TextField(null=True)
#     alternate_via = TextField(null=True)
#     extraction_datetime = fields.DatetimeField(auto_now_add=True, null=True)
#
#     @property
#     def extraction_datetime_ec(self):
#         """
#         Devuelve `extraction_datetime` convertido a la zona horaria de Ecuador.
#         """
#         if self.extraction_datetime:
#             return self.extraction_datetime.astimezone(ecuador_tz)
#         return None
#
#     class Meta:
#         table = "vias_ec"
#
#     def __str__(self):
#         return f"Vía: {self.province} > {self.via} > {self.state}"
class ViaEstado(str, Enum):
    ACTIVA = "A"
    INACTIVA = "I"


class Via(Model):

    id = fields.UUIDField(pk=True)

    descripcion = fields.TextField()
    codigo = fields.CharField(max_length=50, null=True)
    observaciones = fields.TextField(null=True)

    estado = fields.CharField(max_length=1,index=True)

    created = fields.DatetimeField(null=True)
    modified = fields.DatetimeField(null=True)

    provincia = fields.ForeignKeyField(
        "models.Provincia",
        related_name="vias"
    )

    canton = fields.ForeignKeyField(
        "models.Canton",
        related_name="vias"
    )

    centro = fields.ForeignKeyField(
        "models.Centro",
        related_name="vias"
    )

    estado_actual = fields.ForeignKeyField(
        "models.EstadoActual",
        related_name="vias"
    )

    categoria = fields.ForeignKeyField(
        "models.CategoriaVia",
        related_name="vias"
    )

    vias_alternas = fields.ManyToManyField(
        "models.Via",
        related_name="vias_principales",
        through="via_alternas"
    )

    class Meta:
        table = "vias"

class ViaAlterna(Model):

    id = fields.UUIDField(pk=True)

    via = fields.ForeignKeyField(
        "models.Via",
        related_name="alternas"
    )

    via_alterna = fields.ForeignKeyField(
        "models.Via",
        related_name="principal"
    )

    created = fields.DatetimeField(null=True)

    class Meta:
        table = "via_alternas"
