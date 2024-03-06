from datetime import datetime

from peewee import CharField, IntegerField, ForeignKeyField, BooleanField, DateTimeField
from PO.base import BaseModel
from playhouse.postgres_ext import ArrayField, JSONField

HAS_READ = True
NOT_READ = False

TYPE_SYSTEM = 0
TYPE_PRIVATE_MESSAGE = 1
TYPE_FOLLOW = 2
TYPE_LIKE = 3
TYPE_COMMENT = 4
TYPE_NEW_PROMOTION = 5


class Notification(BaseModel):
    rcver_id = IntegerField()
    text = CharField()
    has_read = BooleanField(default=NOT_READ)
    param = JSONField(default={})
    type = IntegerField()

    class Meta:
        table_name = "notification"
