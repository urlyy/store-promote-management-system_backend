from datetime import datetime

from peewee import CharField, IntegerField, ForeignKeyField, BooleanField, DateTimeField
from PO.base import BaseModel
from playhouse.postgres_ext import  ArrayField

STATUS_WATING = 0
STATUS_PASS = 1
STATUS_FAIL = 2

class Promotion(BaseModel):
    user_id = IntegerField()
    text = CharField()
    imgs = ArrayField(CharField)
    status = IntegerField(default=STATUS_WATING)
    is_top = BooleanField(default=False)

    class Meta:
        table_name = "promotion"
