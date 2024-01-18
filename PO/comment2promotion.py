from datetime import datetime

from peewee import CharField, IntegerField, ForeignKeyField, BooleanField, DateTimeField
from PO.base import BaseModel
from playhouse.postgres_ext import ArrayField

STATUS_WATING = 0
STATUS_PASS = 1
STATUS_FAIL = 2

class Comment2Promotion(BaseModel):
    user_id = IntegerField()
    text = CharField()
    status = IntegerField(default=STATUS_WATING)
    promotion_id = IntegerField()
    class Meta:
        table_name = "comment2promotion"
