from typing import Union
from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.params import Form, Header, File
from peewee import JOIN
from datetime import datetime
from PO.user import User as DB_User, ROLE_MERCHANT, ROLE_ADMIN
from PO.follow_relation import FollowRelation as DB_FollowRelation
from DO.response import Response
from utils import my_jwt, file_util
from PO.comment2merchant import Comment2Merchant as DB_Comment2Merchant
from PO.merchant_meta import MerchantMeta as DB_MerchantMeta
import recommend

router = APIRouter()


@router.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    db_user: DB_User = DB_User.select().where(
        (DB_User.username == username) & (DB_User.is_deleted == False)).first()
    if db_user is None:
        return Response.fail(message="不存在该用户或用户已被封禁")
    DB_MerchantMeta.select().where(DB_MerchantMeta.user_id == db_user.id)
    token = my_jwt.create_jwt(db_user.id)
    user = {
        "id": db_user.id,
        "username": db_user.username,
        "brief": db_user.brief,
        "avatar": db_user.avatar,
        "role": db_user.role,
        "fanNum": db_user.fan_num,
        "gender": db_user.gender,
        "age": db_user.age,
    }
    if db_user.role == ROLE_MERCHANT:
        db_merchant = DB_MerchantMeta.select().where(DB_MerchantMeta.user_id == db_user.id).first()
        user['location'] = db_merchant.location
        user['promotionNum'] = db_merchant.promotion_num
        user['commentNum'] = db_merchant.comment_num
        user['category'] = db_merchant.category
    # 更新最新时间
    DB_User.update(last_login=datetime.now()).where(DB_User.id == db_user.id).execute()
    return Response.ok({"user": user, "token": token})


@router.post("/register")
async def register(username: str = Form(...), password: str = Form(...), gender: str = Form(...)):
    db_user: DB_User = DB_User.select().where(DB_User.username == username).first()
    if db_user is not None:
        return Response.fail(message="该用户名已被占用")
    DB_User(username=username, password=password, gender=gender).save()
    recommend.retrain()
    return Response.ok()


@router.post("/password")
async def update_password(old: str = Form(...), new: str = Form(...), authorization: Union[str, None] = Header(None)):
    my_id = my_jwt.get_user_id(authorization)
    db_user = DB_User.select().where(DB_User.id == my_id).first()
    if db_user.password != old:
        return Response.fail(message="旧密码错误")
    DB_User.update(password=new).where(DB_User.id == my_id).execute()
    return Response.ok()


@router.post("/profile")
async def update_profile(username: str, brief: str, age: int, gender: bool,
                         authorization: Union[str, None] = Header(None)):
    my_id = my_jwt.get_user_id(authorization)
    db_user = DB_User.select().where(DB_User.username == username).first()
    if db_user != None and db_user.id != my_id and db_user.username == username:
        return Response.fail(message="该用户名已被占用")
    DB_User.update(username=username, brief=brief, age=age, gender=gender).where(DB_User.id == my_id).execute()
    return Response.ok()


@router.post("/avatar")
async def change_avatar(file: UploadFile = File(...), authorization: Union[str, None] = Header(None)):
    my_id = my_jwt.get_user_id(authorization)
    url = file_util.save2local(file.file.read(), file.filename)
    DB_User.update(avatar=url).where(DB_User.id == my_id).execute()
    return Response.ok({"avatar": url})


@router.get("/list")
async def search_users(keyword: str, authorization: Union[str, None] = Header(None)):
    my_id = my_jwt.get_user_id(authorization)
    search_res = DB_User.select().where(((DB_User.username.contains(keyword)) | (DB_User.brief.contains(keyword))) & (
                DB_User.is_deleted == False)).limit(10)
    my_follow_ids = []
    sql = DB_FollowRelation.select().where(
        (DB_FollowRelation.fan_id == my_id) & (DB_FollowRelation.is_deleted == False))
    for r in sql:
        my_follow_ids.append(r.user_id)
    users = []
    for u in search_res:
        user = {
            "userId": u.id,
            "username": u.username,
            "avatar": u.avatar,
            "brief": u.brief,
            "follow": u.id in my_follow_ids
        }
        users.append(user)
    return Response.ok(data={"users": users})


@router.get("/{user_id}")
async def get_profile(user_id: int, authorization: Union[str, None] = Header(None)):
    my_id = my_jwt.get_user_id(authorization)
    db_user = DB_User.select().where(DB_User.id == user_id).first()
    assert db_user != None
    is_following = False
    if my_id != None:
        res = DB_FollowRelation.select().where(
            (DB_FollowRelation.user_id == user_id) & (DB_FollowRelation.fan_id == my_id)).first()
        is_following = res != None
    user = {
        "id": db_user.id,
        "username": db_user.username,
        "brief": db_user.brief,
        "avatar": db_user.avatar,
        "age": db_user.age,
        "gender": db_user.gender,
        "role": db_user.role,
        'fanNum': db_user.fan_num,
        'follow': is_following,
    }
    if db_user.role == ROLE_MERCHANT:
        db_merchant = DB_MerchantMeta.select().where(DB_MerchantMeta.user_id == db_user.id).first()
        user['location'] = db_merchant.location
        user['promotionNum'] = db_merchant.promotion_num
        user['commentNum'] = db_merchant.comment_num
        user['category'] = db_merchant.category
    return Response.ok({"user": user})


@router.get("/{user_id}/follow/list")
async def get_follow_list(user_id: int, authorization: Union[str, None] = Header(None)):
    my_id = my_jwt.get_user_id(authorization)
    # 查他的用户
    sql_1 = DB_FollowRelation.select(DB_User.id, DB_User.avatar, DB_User.username, DB_User.brief) \
        .where((DB_FollowRelation.fan_id == user_id) & (DB_FollowRelation.is_deleted == False)) \
        .join(
        DB_User, JOIN.LEFT_OUTER,
        on=(DB_User.id == DB_FollowRelation.user_id)
    ).order_by(DB_FollowRelation.create_time.desc())
    users = []
    for u in sql_1.dicts():
        user = {
            'userId': u['id'],
            'username': u['username'],
            'avatar': u['avatar'],
            'brief': u['brief'],
            'follow': False
        }
        users.append(user)
    # 查我的
    sql_2 = DB_FollowRelation.select(DB_FollowRelation.user_id) \
        .where((DB_FollowRelation.fan_id == my_id) & (DB_FollowRelation.is_deleted == False))
    my_follows = list(map(lambda u: u.user_id, list(sql_2)))
    for u in users:
        if u['userId'] in my_follows:
            u["follow"] = True
    return Response.ok(data={"users": users})


@router.post("/follow/{user_id}")
async def follow(user_id: int, authorization: Union[str, None] = Header(None)):
    my_id = my_jwt.get_user_id(authorization)
    db_user = DB_User.select().where(DB_User.id == user_id).first()
    res = DB_FollowRelation.select().where(
        (DB_FollowRelation.user_id == user_id) & (DB_FollowRelation.fan_id == my_id)).first()
    if res == None:
        DB_FollowRelation(fan_id=my_id, user_id=user_id).save()
        DB_User.update(fan_num=db_user.fan_num + 1).where(DB_User.id == user_id).execute()
    else:
        if res.is_deleted == True:
            DB_FollowRelation.update(is_deleted=False).where(DB_FollowRelation.id == res.id).execute()
            DB_User.update(fan_num=db_user.fan_num + 1).where(DB_User.id == user_id).execute()
    return Response.ok()


@router.post("/follow_cancel/{user_id}")
async def follow_cancel(user_id: int, authorization: Union[str, None] = Header(None)):
    my_id = my_jwt.get_user_id(authorization)
    db_user = DB_User.select().where(DB_User.id == user_id).first()
    res = DB_FollowRelation.select().where(
        (DB_FollowRelation.user_id == user_id) & (DB_FollowRelation.fan_id == my_id)).first()
    if res != None:
        if res.is_deleted == False:
            DB_FollowRelation.update(is_deleted=True).where(DB_FollowRelation.id == res.id).execute()
            DB_User.update(fan_num=db_user.fan_num - 1).where(DB_User.id == user_id).execute()
    return Response.ok()


@router.get("/{user_id}/merchant/comment")
async def get_comment2merchant(user_id: int, authorization: Union[str, None] = Header(None)):
    my_id = my_jwt.get_user_id(authorization)
    user_id_set = set()
    db_comments = DB_Comment2Merchant.select(DB_User, DB_Comment2Merchant).where(
        (DB_Comment2Merchant.user_id == user_id) & (DB_Comment2Merchant.status == 1)).join(DB_User,
                                                                                           on=DB_User.id == DB_Comment2Merchant.merchant_id).order_by(
        DB_Comment2Merchant.create_time.desc())
    for c in db_comments:
        user_id_set.add(c.user_id)
    user_dict = {}
    for id in user_id_set:
        user = DB_User.select().where(DB_User.id == id).first()
        user_dict[id] = user
    comments = []
    for c in db_comments:
        u = user_dict[c.user_id]
        comment = {
            'id': c.id,
            'userId': u.id,
            'text': c.text,
            'merchantId': c.merchant_id,
            'merchantUsername': c.user.username,
            'createTime': c.create_time,
            'imgs': c.imgs,
            'star': c.star,
            'avatar': u.avatar,
            'username': u.username,
        }
        comments.append(comment)
    return Response.ok(data={"comments": comments})
