from typing import Union, List

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.params import Form, Header, File
from peewee import JOIN

from PO.user import User as DB_User, ROLE_MERCHANT
from DO.user import User
from PO.promotion import Promotion as DB_Promotion
from DO.response import Response
from utils import my_jwt, file_util
from PO.comment2promotion import Comment2Promotion as DB_Comment2Promotion
from DO.comment2promotion import Comment2Promotion
from PO.like2promotion import Like2Promotion as DB_Like2Promotion


router = APIRouter()


@router.post("")
async def create_promotion(text=Form(...), files: List[UploadFile] = [],
                           authorization: Union[str, None] = Header(None)):
    user_id = my_jwt.get_user_id(authorization)
    urls = []
    for file in files:
        url = file_util.save2local(file.file.read(), file.filename)
        urls.append(url)
    DB_Promotion(user_id=user_id, text=text, imgs=urls).save()
    return Response.ok()


@router.get("/recommend")
async def get_promotions(keyword: str = "", category: int = 0, authorization: Union[str, None] = Header(None)):
    user_id = my_jwt.get_user_id(authorization)
    print(keyword, category)
    sql = DB_Promotion.select().order_by(DB_Promotion.create_time.desc())
    prmotions = list(sql.dicts())
    return Response.ok(data={"promotions": prmotions})


@router.get("/user/{user_id}")
async def get_merchant_promotion(user_id: int, authorization: Union[str, None] = Header(None)):
    my_id = my_jwt.get_user_id(authorization)
    sql = DB_Promotion.select().where(DB_Promotion.user_id == user_id).order_by(DB_Promotion.create_time.desc())
    prmotions = list(sql.dicts())
    return Response.ok(data={"promotions": prmotions})

@router.get("/{promotion_id}")
async def get_promotion(promotion_id: int, authorization: Union[str, None] = Header(None)):
    my_id = my_jwt.get_user_id(authorization)
    db_promotion = DB_Promotion.select().where(DB_Promotion.id == promotion_id).first()
    assert db_promotion != None
    return Response.ok(data = {"promotion": db_promotion.__data__})


@router.post("/{promotion_id}/comment")
async def create_comment2promotion(promotion_id: int, text: str = Form(...),
                                   authorization: Union[str, None] = Header(None)):
    user_id = my_jwt.get_user_id(authorization)
    db_c2p = DB_Comment2Promotion(user_id=user_id, text=text, promotion_id=promotion_id)
    db_c2p.save()
    c2p = Comment2Promotion.from_po(db_c2p)
    return Response.ok(data={"comment": c2p})


@router.get("/{promotion_id}/comment")
async def get_comment2promotion(promotion_id: int, authorization: Union[str, None] = Header(None)):
    user_id = my_jwt.get_user_id(authorization)
    sql = DB_Comment2Promotion.select().where(DB_Comment2Promotion.promotion_id == promotion_id)
    comments = list(sql.dicts())
    return Response.ok(data={"comments": comments})


@router.get("/{promotion_id}/like")
async def get_like_list(promotion_id:int,authorization: Union[str, None] = Header(None)):
    my_id = my_jwt.get_user_id(authorization)
    sql = DB_Like2Promotion.select(DB_User.user_id,DB_User.username,DB_User.avatar).where(DB_Like2Promotion.promotion_id == promotion_id).join(DB_User, JOIN.LEFT_OUTER, on=(
                DB_User.id == DB_FollowRelation.user_id))
    users = list(sql.dicts())
    return Response.ok(data={"users":users})

@router.post("/{promotion_id}/like")
async def like(user_id: int, authorization: Union[str, None] = Header(None)):
    my_id = my_jwt.get_user_id(authorization)
    db_user = DB_User.select().where(DB_User.id == user_id).first()
    assert db_user != None
    DB_FollowRelation(user_id=user_id, fan_id=my_id).save()
    return Response.ok()


@router.post("/{promotion_id}/like_cancel")
async def like_cancel(user_id: int, authorization: Union[str, None] = Header(None)):
    my_id = my_jwt.get_user_id(authorization)
    db_user = DB_User.select().where(DB_User.id == user_id).first()
    assert db_user != None
    DB_FollowRelation().delete().where((DB_FollowRelation.user_id == user_id) & (DB_FollowRelation.fan_id == my_id)).execute()
    return Response.ok()
