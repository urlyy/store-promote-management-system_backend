import random
from datetime import datetime

from faker import Faker
from peewee import PostgresqlDatabase, Model, CharField, IntegerField, ForeignKeyField, DateTimeField, AutoField, \
    BooleanField
from playhouse.shortcuts import ReconnectMixin
from playhouse.pool import PooledPostgresqlDatabase
from playhouse.postgres_ext import PostgresqlExtDatabase
from PO import user, promotion, follow_relation, comment2promotion, comment2merchant, like2promotion, merchant_meta
from datetime import datetime, timedelta
from utils import config

c = config.get("postgres")
# 替换为你的数据库连接信息
db = PostgresqlExtDatabase(c['database'], host=c['host'], user=c['user'], password=c['password'])


def clear():
    user.User.delete().execute()
    promotion.Promotion.delete().execute()
    follow_relation.FollowRelation.delete().execute()
    comment2merchant.Comment2Merchant.delete().execute()
    comment2promotion.Comment2Promotion.delete().execute()
    like2promotion.Like2Promotion.delete().execute()
    merchant_meta.MerchantMeta.delete().execute()

    # 重置序列

    db.execute_sql('ALTER SEQUENCE "user_id_seq" RESTART WITH 1;')
    db.execute_sql('ALTER SEQUENCE "promotion_id_seq" RESTART WITH 1;')
    db.execute_sql('ALTER SEQUENCE "follow_relation_id_seq" RESTART WITH 1;')
    db.execute_sql('ALTER SEQUENCE "comment2merchant_id_seq" RESTART WITH 1;')
    db.execute_sql('ALTER SEQUENCE "comment2promotion_id_seq" RESTART WITH 1;')
    db.execute_sql('ALTER SEQUENCE "like2promotion_id_seq" RESTART WITH 1;')
    db.execute_sql('ALTER SEQUENCE "merchant_meta_id_seq" RESTART WITH 1;')


def randint(l, r):
    return random.randint(l, r)


def randtext():
    fake = Faker()
    text = fake.paragraph(nb_sentences=random.randint(3, 8), ext_word_list=None)
    return text


def insert():
    start_time = datetime.now()
    USER_NUM = 500
    MERCHANT_NUM = 100
    PROMOTION_NUM = 1000

    user_ids = list(range(1, USER_NUM + 1))
    # 随机选100个
    merchant_ids = random.sample(user_ids, MERCHANT_NUM)
    # merchant_ids = list(map(lambda m: m.id, merchant_meta.MerchantMeta.select()))
    promotion_ids = list(range(1, PROMOTION_NUM + 1))
    print("start create user...")
    # user
    for i in user_ids:
        age = randint(18, 70)
        gender = random.choice([True, False])
        user.User(username=f"user-{i}", password="1234", gender=gender, age=age, fan_num=randint(20, USER_NUM / 2),
                  avatar="https://picx.zhimg.com/80/v2-9fe889ce22e86781ed9da41d371a3980_1440w.webp?source=2c26e567").save()
    # merchant
    print("start create merchant...")
    for id in merchant_ids:
        category = random.choice(merchant_meta.CATEGORIES)
        location = [round(random.uniform(27.0, 28.0), 6), round(random.uniform(111.0, 112.0), 6)]
        user.User.update(role=user.ROLE_MERCHANT).where(user.User.id == id).execute()
        merchant_meta.MerchantMeta(user_id=id, promotion_num=randint(20, 130), comment_num=randint(5, 20),
                                   location=location, category=category).save()
    # follow_relation
    print("start create follow_relation...")
    fan_ids = random.sample(user_ids, 350)
    for id in fan_ids:
        target_ids = random.sample(merchant_ids, randint(1, 40))
        for target in target_ids:
            follow_relation.FollowRelation(user_id=target, fan_id=id).save()
    # promotion
    print("start create promotion...")
    for id in promotion_ids:
        text = randtext()
        merchant_id = random.choice(merchant_ids)
        promotion.Promotion(merchant_id=merchant_id, text=text, comment_num=randint(3, 10),
                            like_num=randint(5, 25), imgs=[], status=1).save()
    # like2promotion
    print("start create like2promotion...")
    promotions = list(promotion.Promotion.select())
    for p in promotions:
        liker_ids = random.sample(user_ids, p.like_num)
        for id in liker_ids:
            like2promotion.Like2Promotion(user_id=id, promotion_id=p.id, merchant_id=p.merchant_id).save()
    # comment2merchant
    print("start create comment2merchant...")
    merchants = list(merchant_meta.MerchantMeta.select())
    for m in merchants:
        ids = random.sample(user_ids, m.comment_num)
        for id in ids:
            comment2merchant.Comment2Merchant(user_id=id, status=1, merchant_id=m.user_id, text=randtext(),
                                              star=randint(1, 5), imgs=[]).save()
    # comment2promotion
    print("start create comment2promotion...")
    for p in promotions:
        ids = random.sample(user_ids, p.comment_num)
        for id in ids:
            comment2promotion.Comment2Promotion(user_id=id, status=1, promotion_id=p.id, text=randtext(),
                                                merchant_id=p.merchant_id).save()
    print("结束")
    end_time = datetime.now()
    print(f"花费{(end_time - start_time).seconds}秒")

# 单次耗时17min左右
# clear()
# insert()
