from datetime import datetime

from peewee import CharField, IntegerField, ForeignKeyField, BooleanField, DateTimeField
from PO.base import BaseModel
from playhouse.postgres_ext import  ArrayField

STATUS_WAITING = 0
STATUS_PASS = 1
STATUS_FAIL = 2

class Promotion(BaseModel):
    merchant_id = IntegerField()
    text = CharField()
    imgs = ArrayField(CharField)
    status = IntegerField(default=STATUS_WAITING)
    is_top = BooleanField(default=False)
    comment_num = IntegerField(default=0)
    like_num = IntegerField(default=0)

    class Meta:
        table_name = "promotion"
