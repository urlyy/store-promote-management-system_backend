from datetime import datetime

from peewee import CharField, IntegerField, ForeignKeyField, BooleanField, DateTimeField, FloatField
from PO.base import BaseModel
from playhouse.postgres_ext import ArrayField

ROLE_USER = 0
ROLE_MERCHANT = 1
ROLE_ADMIN = 2

GENDER_FEMALE = True
GENDER_MALE = False


class User(BaseModel):
    username = CharField(unique=True)
    password = CharField()
    avatar = CharField(default="https://picx.zhimg.com/80/v2-9fe889ce22e86781ed9da41d371a3980_1440w.webp?source=2c26e567")
    gender = BooleanField()
    age = IntegerField(default=18)
    brief = CharField(default="这是一条简介")
    role = IntegerField(default=ROLE_USER)
    last_login = DateTimeField(default=datetime.now, verbose_name="添加时间")
    fan_num = IntegerField(default=0)

    class Meta:
        table_name = "user"