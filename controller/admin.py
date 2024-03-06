import math
from datetime import datetime
from functools import reduce
from typing import Union

from fastapi import APIRouter, HTTPException
from fastapi.params import Form, Header
from peewee import fn

from PO.user import User as DB_User, ROLE_ADMIN, ROLE_MERCHANT, ROLE_USER
from DO.response import Response
from utils import my_jwt

from PO.user import User as DB_User
from PO.promotion import Promotion as DB_Promotion, STATUS_PASS, STATUS_FAIL
from PO.comment2merchant import Comment2Merchant as DB_Comment2Merchant
from PO.comment2promotion import Comment2Promotion as DB_Comment2Promotion
from PO.merchant_meta import MerchantMeta as DB_MerchantMeta
from PO.notification import Notification as DB_Notification, TYPE_NEW_PROMOTION
from PO.follow_relation import FollowRelation as DB_FollowRelation
from PO.like2promotion import Like2Promotion as DB_Like2Promotion
from snownlp import SnowNLP

router = APIRouter()

USERS_PAGE_SIZE = 20


@router.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    db_user = DB_User.select().where(
        (DB_User.is_deleted == False) & (DB_User.username == username) & (DB_User.role != ROLE_USER)).first()
    if db_user is None:
        return Response.fail(message="不存在该用户或用户无进入权限")
    token = my_jwt.create_jwt(db_user.id)
    user = {
        "id": db_user.id,
        'username': db_user.username,
        "avatar": db_user.avatar,
        "role": db_user.role,
    }
    DB_User.update(last_login=datetime.now()).where(DB_User.id == db_user.id).execute()
    return Response.ok({"user": user, "token": token})


@router.get("/users")
async def get_users(page_num: int = 1):
    sql = DB_User.select().order_by(DB_User.id.desc()).offset((page_num - 1) * USERS_PAGE_SIZE).limit(USERS_PAGE_SIZE)
    users = []
    for row in sql:
        user = {
            'id': row.id,
            'username': row.username,
            'avatar': row.avatar,
            'creatTime': row.create_time,
            'brief': row.brief,
            'role': row.role,
            'isDeleted': row.is_deleted,
            'lastLogin': row.last_login,
            'fanNum': row.fan_num
        }
        users.append(user)
    count = DB_User.select(fn.COUNT(DB_User.id)).scalar()
    total_page = math.ceil(count / USERS_PAGE_SIZE)
    return Response.ok({"users": users, 'totalPage': total_page, 'pageSize': USERS_PAGE_SIZE})


@router.get("/merchants")
async def get_merchants(page_num: int = 1):
    sql = DB_User.select(DB_User, DB_MerchantMeta).where(DB_User.role == ROLE_MERCHANT).order_by(DB_User.id.desc()) \
        .join(DB_MerchantMeta, on=DB_User.id == DB_MerchantMeta.user_id) \
        .offset((page_num - 1) * USERS_PAGE_SIZE).limit(USERS_PAGE_SIZE)

    merchants = []
    for row in sql:
        u, m = row, row.merchantmeta
        merchant = {
            'userId': u.id,
            'username': u.username,
            'avatar': u.avatar,
            'creatTime': u.create_time,
            'brief': u.brief,
            'isDeleted': u.is_deleted,
            'lastLogin': u.last_login,
            'fanNum': u.fan_num,
            'promotionNum': m.promotion_num,
            'comment_num': m.comment_num,
            'category': m.category,
            'location': m.location,
        }
        merchants.append(merchant)
    count = DB_User.select(fn.COUNT(DB_User.id)).where(DB_User.role == ROLE_MERCHANT).scalar()
    total_page = math.ceil(count / USERS_PAGE_SIZE)
    return Response.ok({"merchants": merchants, 'totalPage': total_page, 'pageSize': USERS_PAGE_SIZE})


@router.get("/promotions")
async def get_promotions(page_num: int = 1):
    sql = DB_Promotion.select().order_by(DB_Promotion.id.desc()).offset((page_num - 1) * USERS_PAGE_SIZE).limit(
        USERS_PAGE_SIZE)
    promotions = []
    for row in sql:
        promotion = {
            "id": row.id,
            "merchantId": row.merchant_id,
            "text": row.text,
            "imgs": row.imgs,
            "createTime": row.create_time,
            "commentNum": row.comment_num,
            "likeNum": row.like_num,
            "status": row.status,
            "isDeleted": row.is_deleted,
            "isTop": row.is_top,
        }
        promotions.append(promotion)
    count = DB_Promotion.select(fn.COUNT(DB_Promotion.id)).scalar()
    total_page = math.ceil(count / USERS_PAGE_SIZE)
    return Response.ok({"promotions": promotions, 'totalPage': total_page, 'pageSize': USERS_PAGE_SIZE})


@router.get("/comments/promotion")
async def get_comments2promotion(page_num: int = 1):
    sql = DB_Comment2Promotion.select().order_by(DB_Comment2Promotion.id.desc()).offset(
        (page_num - 1) * USERS_PAGE_SIZE).limit(USERS_PAGE_SIZE)
    comments = []
    for row in sql:
        comment = {
            "id": row.id,
            "text": row.text,
            "createTime": row.create_time,
            "isDeleted": row.is_deleted,
            # "star": row.star,
            "status": row.status,
            "promotionId": row.promotion_id,
            "userId": row.user_id,
            "merchantId": row.merchant_id,
        }
        comments.append(comment)
    count = DB_Comment2Promotion.select(fn.COUNT(DB_Comment2Promotion.id)).scalar()
    total_page = math.ceil(count / USERS_PAGE_SIZE)
    return Response.ok({"comments": comments, 'totalPage': total_page, 'pageSize': USERS_PAGE_SIZE})


@router.get("/comments/merchant")
async def get_comments2merchant(page_num: int = 1):
    sql = DB_Comment2Merchant.select().order_by(DB_Comment2Merchant.id.desc()).offset(
        (page_num - 1) * USERS_PAGE_SIZE).limit(USERS_PAGE_SIZE)
    comments = []
    for row in sql:
        comment = {
            "id": row.id,
            "text": row.text,
            "imgs": row.imgs,
            "createTime": row.create_time,
            "isDeleted": row.is_deleted,
            "star": row.star,
            "status": row.status,
            "userId": row.user_id,
            "merchantId": row.merchant_id,
        }
        comments.append(comment)
    count = DB_Comment2Merchant.select(fn.COUNT(DB_Comment2Merchant.id)).scalar()
    total_page = math.ceil(count / USERS_PAGE_SIZE)
    return Response.ok({"comments": comments, 'totalPage': total_page, 'pageSize': USERS_PAGE_SIZE})


@router.delete("/user/{user_id}")
async def delete_user(user_id: int):
    DB_User.update(is_deleted=True).where(DB_User.id == user_id).execute()
    return Response.ok()


@router.put("/user/{user_id}")
async def recover_delete_user(user_id: int):
    DB_User.update(is_deleted=False).where(DB_User.id == user_id).execute()
    return Response.ok()


@router.post("/promotion/pass/{promotion_id}")
async def pass_promotion(promotion_id: int):
    p = DB_Promotion.select().where(DB_Promotion.id == promotion_id).first()
    # 新推广
    is_new = False
    if p.status == 0:
        is_new = True
    m = DB_User.select().where(DB_User.id == p.merchant_id).first()
    DB_Promotion.update(status=STATUS_PASS).where(DB_Promotion.id == promotion_id).execute()
    fans = DB_FollowRelation.select().where(DB_FollowRelation.user_id == m.id)
    if is_new:
        for fan in fans:
            DB_Notification(text=f"你关注的商户{m.username}发布了新推广", rcver_id=fan.fan_id, type=TYPE_NEW_PROMOTION,
                            param={'promotionId': p.id, "merchantId": p.merchant_id}).save()
    return Response.ok()


@router.get("/merchant/data")
async def get_merchant_data(authorization: Union[str, None] = Header(None)):
    # 准备数据
    my_id = my_jwt.get_user_id(authorization)
    user = DB_User.select().where(DB_User.id == my_id).first()
    merchant = DB_MerchantMeta.select().where(DB_MerchantMeta.user_id == my_id).first()
    promotions = list(
        DB_Promotion.select().where((DB_Promotion.merchant_id == my_id) & (DB_Promotion.is_deleted == False)))
    comment2promotion_num = reduce(lambda a, b: a + b.comment_num, promotions, 0)
    promotion_like_num = reduce(lambda a, b: a + b.like_num, promotions, 0)
    max_like_promotion = max(promotions, key=lambda obj: obj.like_num)
    max_comment_promotion = max(promotions, key=lambda obj: obj.comment_num)
    sql = DB_Comment2Merchant.select().where(DB_Comment2Merchant.merchant_id == my_id)
    stars = [0, 0, 0, 0, 0]
    sentiments = [0, 0]
    for row in sql:
        stars[row.star - 1] += 1
        score = SnowNLP(row.text).sentiments
        if score > 0.5:
            sentiments[1] += 1
        else:
            sentiments[0] += 1
    average_promotion_num = DB_MerchantMeta \
        .select(fn.AVG(DB_MerchantMeta.promotion_num).alias('average'))[0].average

    def trans_promotion(p):
        return {
            "id": p.id,
            "text": p.text,
            "imgs": p.imgs,
            "createTime": p.create_time,
        }

    data = {
        "promotionNum": merchant.promotion_num,
        "averagePromotionNum": round(average_promotion_num, 2),
        "fanNum": user.fan_num,
        "comment2merchantNum": merchant.comment_num,
        "comment2promotionNum": comment2promotion_num,
        "promotionLikeNum": promotion_like_num,
        "maxLikePromotion": trans_promotion(max_like_promotion),
        "maxCommentPromotion": trans_promotion(max_comment_promotion),
        "stars": stars,
        "comment2merchantSentiments":sentiments
    }
    return Response.ok(data={"data": data})


@router.post("/promotion/deny/{promotion_id}")
async def deny_promotion(promotion_id: int):
    DB_Promotion.update(status=STATUS_FAIL).where(DB_Promotion.id == promotion_id).execute()
    return Response.ok()


@router.post("/comment2merchant/pass/{id}")
async def pass_promotion(id: int):
    DB_Comment2Merchant.update(status=STATUS_PASS).where(DB_Comment2Merchant.id == id).execute()
    return Response.ok()


@router.post("/comment2merchant/deny/{id}")
async def deny_promotion(id: int):
    DB_Comment2Merchant.update(status=STATUS_FAIL).where(DB_Comment2Merchant.id == id).execute()
    return Response.ok()


@router.post("/comment2promotion/pass/{id}")
async def pass_promotion(id: int):
    DB_Comment2Promotion.update(status=STATUS_PASS).where(DB_Comment2Promotion.id == id).execute()
    return Response.ok()


@router.post("/comment2promotion/deny/{id}")
async def deny_promotion(id: int):
    DB_Comment2Promotion.update(status=STATUS_FAIL).where(DB_Comment2Promotion.id == id).execute()
    return Response.ok()
