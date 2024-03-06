from peewee import CharField, IntegerField, ForeignKeyField, BooleanField, DateTimeField, FloatField
from PO.base import BaseModel
from playhouse.postgres_ext import ArrayField


CATEGORIES = ["零售","餐饮","服务","娱乐","特色"]
# CATEGORY_lingshou = "零售"
# CATEGORY_canyin =   "餐饮"
# CATEGORY_fuwu =     "服务"
# CATEGORY_yule =     "娱乐"
# CATEGORY_tese =     "特色"


from datetime import datetime

from peewee import CharField, IntegerField, ForeignKeyField, BooleanField, DateTimeField, FloatField
from PO.base import BaseModel
from playhouse.postgres_ext import ArrayField


class MerchantMeta(BaseModel):
    user_id = IntegerField(unique=True)
    promotion_num = IntegerField(default=0)
    comment_num = IntegerField(default=0)
    location = ArrayField(FloatField, dimensions=2)
    category = CharField()

    class Meta:
        table_name = "merchant_meta"
