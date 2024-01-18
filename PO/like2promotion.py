from datetime import datetime

from peewee import CharField, IntegerField, ForeignKeyField, BooleanField, DateTimeField
from PO.base import BaseModel

class Like2Promotion(BaseModel):
    user_id = IntegerField()
    promotion_id = IntegerField()
    class Meta:
        table_name = "like2promotion"
