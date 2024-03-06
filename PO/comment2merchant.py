from datetime import datetime

from peewee import CharField, IntegerField, ForeignKeyField, BooleanField, DateTimeField
from PO.base import BaseModel
from playhouse.postgres_ext import ArrayField

STATUS_WATING = 0
STATUS_PASS = 1
STATUS_FAIL = 2

class Comment2Merchant(BaseModel):
    user_id = IntegerField()
    merchant_id = IntegerField()
    text = CharField()
    star = IntegerField(default=5,db_column="_star")
    imgs = ArrayField(CharField)
    status = IntegerField(default=STATUS_PASS)


    class Meta:
        table_name = "comment2merchant"
