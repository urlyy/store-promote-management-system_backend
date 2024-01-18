from typing import Union, List

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.params import Form, Header, File
from PO.notification import Notification as DB_Notification, NOT_READ, HAS_READ
from DO.response import Response
from utils import my_jwt, file_util

router = APIRouter()


@router.get("/")
async def get_notifications(authorization: Union[str, None] = Header(None)):
    user_id = my_jwt.get_user_id(authorization)
    sql = DB_Notification.select().where(DB_Notification.rcver_id == user_id)
    notifications = list(sql.dicts())
    # 标为已读
    # for noti in notifications:
    #     DB_Notification.update(has_read=HAS_READ).where(noti)
    return Response.ok(data={"notifications": notifications})


@router.get("/count/unread")
async def get_comment2promotion(authorization: Union[str, None] = Header(None)):
    user_id = my_jwt.get_user_id(authorization)
    cnt = DB_Notification.select().where(
        DB_Notification.rcver_id == user_id and DB_Notification.has_read == NOT_READ).count()
    return Response.ok(data={"unread_cnt": cnt})
