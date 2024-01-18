from datetime import datetime

from peewee import CharField, IntegerField, ForeignKeyField, BooleanField, DateTimeField
from PO.base import BaseModel
from playhouse.postgres_ext import ArrayField
from PO.user import User

class FollowRelation(BaseModel):
    user_id = IntegerField()
    fan_id = IntegerField()

    class Meta:
        table_name = "follow_relation"
