import math
from typing import Union, List

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.params import Form, Header, File, Body
from peewee import JOIN, fn

from PO.user import User as DB_User, ROLE_MERCHANT

from PO.promotion import Promotion as DB_Promotion
from DO.response import Response
from utils import my_jwt, file_util
from PO.comment2promotion import Comment2Promotion as DB_Comment2Promotion
from PO.merchant_meta import MerchantMeta as DB_MerchantMeta
from PO.like2promotion import Like2Promotion as DB_Like2Promotion
from recommend import get_recommend_merchant_ids
from PO.follow_relation import FollowRelation as DB_FollowRelation

router = APIRouter()

PROMOTION_PAGE_SIZE = 10


@router.post("")
async def create_promotion(text: str = Body(...), imgs: List[str] = Body(...),
                           authorization: Union[str, None] = Header(None)):
    user_id = my_jwt.get_user_id(authorization)
    DB_Promotion(merchant_id=user_id, text=text, imgs=imgs).save()
    merchant = DB_MerchantMeta.select().where(DB_MerchantMeta.user_id == user_id).first()
    DB_MerchantMeta.update(promotion_num=merchant.promotion_num + 1).where(DB_MerchantMeta.user_id == user_id)
    return Response.ok()


@router.delete("/{promotion_id}")
async def create_promotion(promotion_id: int,
                           authorization: Union[str, None] = Header(None)):
    user_id = my_jwt.get_user_id(authorization)
    DB_Promotion.update(is_deleted=True).where(DB_Promotion.id == promotion_id).execute()
    merchant = DB_MerchantMeta.select().where(DB_MerchantMeta.user_id == user_id).first()
    DB_MerchantMeta.update(promotion_num=merchant.promotion_num - 1).where(DB_MerchantMeta.user_id == user_id)
    return Response.ok()


@router.post("/edit/{promotion_id}")
async def edit_promotion(promotion_id: int, text: str = Body(...), imgs: List[str] = Body(...),
                         authorization: Union[str, None] = Header(None)):
    user_id = my_jwt.get_user_id(authorization)
    DB_Promotion.update(text=text, imgs=imgs).where(DB_Promotion.id == promotion_id).execute()
    return Response.ok()


@router.get("/recommend")
async def get_recommend_promotions(latitude: float, longitude: float, page_num: int, order: int = 0,
                                   category: str = None,
                                   keyword: str = "",
                                   authorization: Union[str, None] = Header(None)):
    user_id = my_jwt.get_user_id(authorization)
    if category == '全部':
        category = None
    promotions = None
    if order == 1:
        sql = DB_MerchantMeta.select(DB_Promotion)
        if category != None:
            sql = sql.where(DB_MerchantMeta.category == category)
        sql = sql.join(DB_Promotion, on=DB_Promotion.merchant_id == DB_MerchantMeta.user_id)
        sql = sql.where(
            (DB_Promotion.text.contains(keyword)) & (DB_Promotion.is_deleted == False) & (DB_Promotion.status == 1))
        res = sql.order_by(DB_Promotion.create_time.desc()).offset((page_num - 1) * PROMOTION_PAGE_SIZE).limit(
            PROMOTION_PAGE_SIZE).execute()
        promotions = list(map(lambda row: row.promotion, res))
    # 走推荐的
    else:
        recommend = get_recommend_merchant_ids(user_id, latitude, longitude, category)
        # 是主动搜索的
        if keyword != "":
            # 还是按关键字查询
            promotions = list(DB_Promotion.select().where(
                (DB_Promotion.text.contains(keyword)) & (DB_Promotion.is_deleted == False) & (
                            DB_Promotion.status == 1)).order_by(
                DB_Promotion.create_time.desc()).offset((page_num - 1) * PROMOTION_PAGE_SIZE).limit(
                PROMOTION_PAGE_SIZE))
            if len(promotions) > 0:
                # 但是推荐的优先放前面
                priorities = []
                for idx in range(len(promotions) - 1, -1, -1):
                    p = promotions[idx]
                    if p.merchant_id in recommend:
                        promotions.pop(idx)
                        priorities.append(p)
                priorities.extend(promotions)
                promotions = priorities
        else:
            # 是首页推荐的
            promotions = list(DB_Promotion.select().where(
                (DB_Promotion.merchant_id.in_(recommend)) & (DB_Promotion.is_deleted == False) & (
                            DB_Promotion.status == 1)).order_by(
                DB_Promotion.create_time.desc()).offset((page_num - 1) * PROMOTION_PAGE_SIZE).limit(
                PROMOTION_PAGE_SIZE))
    res_promotions = []
    for p in promotions:
        pro = {
            'id': p.id,
            'merchantId': p.merchant_id,
            'text': p.text,
            'createTime': p.create_time,
            'imgs': p.imgs,
            'isTop': p.is_top,
            'commentNum': p.comment_num,
            'likeNum': p.like_num,
        }
        res_promotions.append(pro)
    return Response.ok(
        data={"promotions": res_promotions, "pageNum": page_num, "noMore": len(promotions) != PROMOTION_PAGE_SIZE})


@router.get("/follow")
async def get_follow_promotions(page_num: int, authorization: Union[str, None] = Header(None)):
    user_id = my_jwt.get_user_id(authorization)
    res = DB_FollowRelation.select(DB_Promotion).where(
        (DB_FollowRelation.fan_id == user_id) & (DB_FollowRelation.is_deleted == False)) \
        .join(DB_Promotion, on=DB_Promotion.merchant_id == DB_FollowRelation.user_id) \
        .where((DB_Promotion.is_deleted == False) & (DB_Promotion.status == 1)) \
        .offset((page_num - 1) * PROMOTION_PAGE_SIZE).limit(PROMOTION_PAGE_SIZE) \
        .order_by(DB_Promotion.create_time.desc()).execute()
    # 走推荐的
    res_promotions = []
    for row in res:
        promotion = row.promotion
        pro = {
            'id': promotion.id,
            'merchantId': promotion.merchant_id,
            'text': promotion.text,
            'createTime': promotion.create_time,
            'imgs': promotion.imgs,
            'isTop': promotion.is_top,
            'commentNum': promotion.comment_num,
            'likeNum': promotion.like_num,
        }
        res_promotions.append(pro)
    return Response.ok(
        data={"promotions": res_promotions, "pageNum": page_num, "noMore": len(res_promotions) != PROMOTION_PAGE_SIZE})


@router.delete("/{promotion_id}")
async def remove_promotion(promotion_id: int, authorization: Union[str, None] = Header(None)):
    my_id = my_jwt.get_user_id(authorization)
    db_promotion = DB_Promotion.select().where(DB_Promotion.id == promotion_id).first()
    if db_promotion.merchant_id == my_id:
        DB_Promotion.update(is_deleted=True).where(DB_Promotion.id == promotion_id).execute()
        merchant = DB_MerchantMeta.select().where(DB_MerchantMeta.user_id == my_id).first()
        DB_MerchantMeta.update(promotion_num=merchant.promotion_num - 1).where(
            DB_MerchantMeta.id == merchant.id).execute()
        return Response.ok()
    else:
        return Response.fail()


@router.get("/user/{user_id}")
async def get_merchant_promotions(user_id: int, authorization: Union[str, None] = Header(None)):
    my_id = my_jwt.get_user_id(authorization)
    sql = DB_Promotion.select().where(
        (DB_Promotion.merchant_id == user_id) & (DB_Promotion.is_deleted == False) & (
                    DB_Promotion.status == 1)).order_by(
        DB_Promotion.create_time.desc())
    promotions = []
    for p in sql:
        pro = {
            'id': p.id,
            'merchantId': p.merchant_id,
            'createTime': p.create_time,
            'imgs': p.imgs,
            'isTop': p.is_top,
            'commentNum': p.comment_num,
            'likeNum': p.like_num,
            'text': p.text,
        }
        promotions.append(pro)
    return Response.ok(data={"promotions": promotions})


@router.get("/merchant/all")
async def get_merchant_all_promotions(page_num: int = 1, authorization: Union[str, None] = Header(None)):
    my_id = my_jwt.get_user_id(authorization)
    sql = DB_Promotion.select().where(
        (DB_Promotion.merchant_id == my_id) & (DB_Promotion.is_deleted == False)).order_by(
        DB_Promotion.create_time.desc()).offset((page_num - 1) * PROMOTION_PAGE_SIZE).limit(PROMOTION_PAGE_SIZE)
    promotions = []
    for p in sql:
        pro = {
            'id': p.id,
            'merchantId': p.merchant_id,
            'createTime': p.create_time,
            'imgs': p.imgs,
            'isTop': p.is_top,
            'commentNum': p.comment_num,
            'likeNum': p.like_num,
            'text': p.text,
            "isDeleted": p.is_deleted,
            'status': p.status,
        }
        promotions.append(pro)
    count = DB_Promotion.select(fn.COUNT(DB_Promotion.id)).where(
        (DB_Promotion.merchant_id == my_id) & (DB_Promotion.is_deleted == False)).scalar()
    total_page = math.ceil(count / PROMOTION_PAGE_SIZE)
    return Response.ok({"promotions": promotions, 'totalPage': total_page, 'pageSize': PROMOTION_PAGE_SIZE})


@router.get("/{promotion_id}")
async def get_promotion(promotion_id: int, authorization: Union[str, None] = Header(None)):
    my_id = my_jwt.get_user_id(authorization)
    db_promotion = DB_Promotion.select().where(DB_Promotion.id == promotion_id).first()
    assert db_promotion != None
    like_record = DB_Like2Promotion.select().where(
        (DB_Like2Promotion.promotion_id == promotion_id) & (DB_Like2Promotion.user_id == my_id)).first()
    print(like_record)
    if like_record != None and like_record.is_deleted == False:
        like = True
    else:
        like = False
    pro = {
        'id': db_promotion.id,
        'merchantId': db_promotion.merchant_id,
        'createTime': db_promotion.create_time,
        'imgs': db_promotion.imgs,
        'isTop': db_promotion.is_top,
        'commentNum': db_promotion.comment_num,
        'likeNum': db_promotion.like_num,
        'text': db_promotion.text,
        'like': like
    }
    return Response.ok(data={"promotion": pro})


@router.post("/{promotion_id}/comment")
async def create_comment2promotion(promotion_id: int, text: str = Form(...),
                                   authorization: Union[str, None] = Header(None)):
    user_id = my_jwt.get_user_id(authorization)
    promotion = DB_Promotion.select().where(DB_Promotion.id == promotion_id).first()
    db_c2p = DB_Comment2Promotion(user_id=user_id, text=text, promotion_id=promotion_id,
                                  merchant_id=promotion.merchant_id)
    db_c2p.save()
    promotion = DB_Promotion.select().where(DB_Promotion.id == promotion_id).first()
    # TODO 和审核联动
    DB_Promotion.update(comment_num=promotion.comment_num + 1).where(DB_Promotion.id == promotion_id).execute()
    comment = {
        'id': db_c2p.id,
        'text': db_c2p.text,
        'promotionId': db_c2p.promotion_id,
        'merchantId': db_c2p.merchant_id,
        'createTime': db_c2p.create_time,
        'userId': db_c2p.user_id,
    }
    return Response.ok(data={"comment": comment})


@router.get("/{promotion_id}/comment")
async def get_comments2promotion(promotion_id: int, authorization: Union[str, None] = Header(None)):
    user_id = my_jwt.get_user_id(authorization)
    sql = DB_Comment2Promotion.select().where(
        (DB_Comment2Promotion.promotion_id == promotion_id) & (DB_Comment2Promotion.status == 1)).order_by(
        DB_Comment2Promotion.create_time.desc())
    comments = []
    for c in sql:
        comment = {
            'id': c.id,
            'text': c.text,
            'promotionId': c.promotion_id,
            'merchantId': c.merchant_id,
            'createTime': c.create_time,
            'userId': c.user_id,
        }
        comments.append(comment)
    return Response.ok(data={"comments": comments})


@router.get("/{promotion_id}/like")
async def get_like_list(promotion_id: int, authorization: Union[str, None] = Header(None)):
    my_id = my_jwt.get_user_id(authorization)
    sql = DB_Like2Promotion.select(DB_User.user_id, DB_User.username, DB_User.avatar) \
        .where(DB_Like2Promotion.promotion_id == promotion_id) \
        .join(DB_User, JOIN.LEFT_OUTER, on=(DB_User.id == DB_Like2Promotion.user_id))
    users = list(sql.dicts())
    return Response.ok(data={"users": users})


@router.post("/{promotion_id}/like")
async def like_promotion(promotion_id: int, authorization: Union[str, None] = Header(None)):
    my_id = my_jwt.get_user_id(authorization)
    res = DB_Like2Promotion.select().where(
        (DB_Like2Promotion.promotion_id == promotion_id) & (DB_Like2Promotion.user_id == my_id)).first()
    promotion = DB_Promotion.select().where(DB_Promotion.id == promotion_id).first()
    if res == None:
        DB_Like2Promotion(user_id=my_id, promotion_id=promotion_id, merchant_id=promotion.merchant_id).save()
        DB_Promotion.update(like_num=promotion.like_num + 1).where(DB_Promotion.id == promotion_id).execute()
    else:
        if res.is_deleted == True:
            DB_Like2Promotion.update(is_deleted=False).where(DB_Like2Promotion.id == res.id).execute()
            DB_Promotion.update(like_num=promotion.like_num + 1).where(DB_Promotion.id == promotion_id).execute()
    return Response.ok()


@router.post("/{promotion_id}/like_cancel")
async def like_cancel(promotion_id: int, authorization: Union[str, None] = Header(None)):
    my_id = my_jwt.get_user_id(authorization)
    res = DB_Like2Promotion.select().where(
        (DB_Like2Promotion.promotion_id == promotion_id) & (DB_Like2Promotion.user_id == my_id)).first()
    promotion = DB_Promotion.select().where(DB_Promotion.id == promotion_id).first()
    if res != None:
        if res.is_deleted == False:
            DB_Like2Promotion.update(is_deleted=True).where(DB_Like2Promotion.id == res.id).execute()
            DB_Promotion.update(like_num=promotion.like_num - 1).where(DB_Promotion.id == promotion_id).execute()
    return Response.ok()
