from tortoise import fields
from tortoise.fields import TextField, CharField
from tortoise.models import Model


class Vias(Model):
    """
    Modelo Tortoise que representa una fila de "vias_ec".
    """
    id = fields.IntField(pk=True)
    province = CharField(max_length=50)
    via = fields.CharField(max_length=100)
    state = CharField(max_length=50)
    observations = TextField()
    alternate_via = TextField()
    extraction_datetime = fields.DatetimeField(auto_now_add=True)
    page_datetime = fields.DatetimeField(null=True)

    class Meta:
        table = "vias_ec"

    def __str__(self):
        return f"Vía: {self.province} > {self.via} > {self.state}"
