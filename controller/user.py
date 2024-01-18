from typing import Union
from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.params import Form, Header, File
from peewee import JOIN

from PO.user import User as DB_User
from DO.user import User
from PO.follow_relation import FollowRelation as DB_FollowRelation
from DO.response import Response
from utils import my_jwt, file_util
from PO.comment2merchant import Comment2Merchant as DB_Comment2Merchant
from DO.comment2merchant import Comment2Merchant

router = APIRouter()


@router.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    db_user: DB_User = DB_User.select().where(DB_User.username == username).first()
    if db_user is None:
        raise HTTPException(status_code=400, detail="不存在该用户")
    token = my_jwt.create_jwt(db_user.id)
    user = User.from_po(db_user)
    return Response.ok({"user": user, "token": token})


@router.post("/avatar")
async def change_avatar(file: UploadFile = File(...), authorization: Union[str, None] = Header(None)):
    my_id = my_jwt.get_user_id(authorization)
    url = file_util.save2local(file.file.read(), file.filename)
    DB_User.update(avatar=url).where(DB_User.id == my_id).execute()
    return Response.ok({"avatar": url})


@router.get("/{user_id}")
async def get_profile(user_id: int, authorization: Union[str, None] = Header(None)):
    my_id = my_jwt.get_user_id(authorization)
    db_user = DB_User.select().where(DB_User.id == user_id).first()
    assert db_user != None
    is_following = False
    if my_id != None:
        res = DB_FollowRelation.select().where(
            DB_FollowRelation.user_id == user_id and DB_FollowRelation.fan_id == my_id).first()
        is_following = res != None
    user = User.from_po(db_user, is_following)
    return Response.ok({"user": user})


@router.get("/{user_id}/follow/list")
async def get_follow_list(user_id: int, authorization: Union[str, None] = Header(None)):
    my_id = my_jwt.get_user_id(authorization)
    # 查他的用户
    sql_1 = DB_FollowRelation.select(DB_User.id, DB_User.avatar, DB_User.username, DB_User.brief) \
        .where(DB_FollowRelation.fan_id == user_id) \
        .join(
        DB_User, JOIN.LEFT_OUTER,
        on=(DB_User.id == DB_FollowRelation.user_id)
    )
    users = list(sql_1.dicts())
    # 查我的
    sql_2 = DB_FollowRelation.select(DB_FollowRelation.user_id) \
        .where(DB_FollowRelation.fan_id == my_id)
    my_follows = list(map(lambda item: item['user_id'], list(sql_2.dicts())))
    for u in users:
        if u['id'] in my_follows:
            u["follow"] = True
        else:
            u["follow"] = False
    return Response.ok(data={"users": users})


@router.post("/follow/{user_id}")
async def follow(user_id: int, authorization: Union[str, None] = Header(None)):
    my_id = my_jwt.get_user_id(authorization)
    db_user = DB_User.select().where(DB_User.id == user_id).first()
    assert db_user != None
    DB_FollowRelation(user_id=user_id, fan_id=my_id).save()
    return Response.ok()


@router.post("/follow_cancel/{user_id}")
async def follow_cancel(user_id: int, authorization: Union[str, None] = Header(None)):
    my_id = my_jwt.get_user_id(authorization)
    db_user = DB_User.select().where(DB_User.id == user_id).first()
    assert db_user != None
    DB_FollowRelation().delete().where(
        (DB_FollowRelation.user_id == user_id) & (DB_FollowRelation.fan_id == my_id)).execute()
    return Response.ok()


@router.get("/{user_id}/merchant/comment")
async def get_comment2merchant(user_id: int, authorization: Union[str, None] = Header(None)):
    my_id = my_jwt.get_user_id(authorization)
    sql = DB_Comment2Merchant.select().where(DB_Comment2Merchant.user_id == user_id)
    db_comments = list(sql)
    user_id_set = set()
    for c in db_comments:
        user_id_set.add(c.user_id)
    user_dict = {}
    for id in user_id_set:
        user = DB_User.select().where(DB_User.id == id).first()
        user_dict[id] = user
    comments = []
    for c in db_comments:
        comment = Comment2Merchant.from_po(c, user_dict[c.user_id])
        comments.append(comment)
    return Response.ok(data={"comments": comments})
