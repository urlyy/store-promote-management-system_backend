from datetime import datetime

from peewee import CharField, IntegerField, ForeignKeyField, BooleanField, DateTimeField
from PO.base import BaseModel
from playhouse.postgres_ext import  ArrayField

ROLE_USER = 0
ROLE_MERCHANT = 1
ROLE_ADMIN = 2

class User(BaseModel):
    username = CharField(unique=True)
    password = CharField()
    coin = IntegerField(default=0)
    avatar = CharField(default="")
    brief = CharField(default="这是一条简介")
    role = IntegerField(default=ROLE_USER)
    last_login = DateTimeField(default=datetime.now, verbose_name="添加时间")
    location = ArrayField(CharField,dimensions=2)

    class Meta:
        table_name = "user"
