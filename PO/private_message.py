from datetime import datetime

from peewee import CharField, IntegerField, ForeignKeyField, BooleanField, DateTimeField
from PO.base import BaseModel
from playhouse.postgres_ext import ArrayField

HAS_READ = True
NOT_READ = False

class PrivateMessage(BaseModel):
    sender_id = IntegerField()
    rcver_id = IntegerField()
    text = CharField(default="")
    img = CharField(default="")
    has_read = BooleanField(default=NOT_READ)

    class Meta:
        table_name = "private_message"
