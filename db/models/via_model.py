from pytz import timezone
from tortoise import fields
from tortoise.fields import TextField, CharField
from tortoise.models import Model

ecuador_tz = timezone("America/Guayaquil")  # Definir la zona horaria de Ecuador

class Vias(Model):
    """
    Modelo Tortoise que representa una fila de "vias_ec".
    """
    id = fields.IntField(pk=True,auto_increment=True)
    province = CharField(max_length=50)
    via = fields.CharField(max_length=100)
    state = CharField(max_length=50)
    observations = TextField(null=True)
    alternate_via = TextField(null=True)
    extraction_datetime = fields.DatetimeField(auto_now_add=True, null=True)

    @property
    def extraction_datetime_ec(self):
        """
        Devuelve `extraction_datetime` convertido a la zona horaria de Ecuador.
        """
        if self.extraction_datetime:
            return self.extraction_datetime.astimezone(ecuador_tz)
        return None

    class Meta:
        table = "vias_ec"

    def __str__(self):
        return f"Vía: {self.province} > {self.via} > {self.state}"
