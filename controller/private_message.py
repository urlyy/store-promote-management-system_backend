from datetime import datetime
from typing import Union, List

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.params import Form, Header, File
from PO.private_message import PrivateMessage as DB_PrivateMessage

from PO.notification import Notification as DB_Notification, TYPE_PRIVATE_MESSAGE
from PO.user import User as DB_User
from DO.response import Response
from utils import my_jwt, file_util

router = APIRouter()


def save_notification(my_id, user_id):
    u = DB_User.select().where(DB_User.id == my_id).first()
    noti = DB_Notification(rcver_id=user_id, text=f"用户 {u.username} 给你发送了私信", param={"senderId": my_id},
                           type=TYPE_PRIVATE_MESSAGE)
    noti.save()


@router.post("/text")
async def create_text_msg(text: str = Form(...), user_id: int = Form(...),
                          authorization: Union[str, None] = Header(None)):
    my_id = my_jwt.get_user_id(authorization)
    db_message = DB_PrivateMessage(sender_id=my_id, rcver_id=user_id, text=text)
    db_message.save()
    save_notification(my_id, user_id)
    res_msg = {
        "id": db_message.id,
        "createTime": datetime.now(),
        "text": db_message.text,
        "img": db_message.img,
        "senderId": my_id,
    }
    return Response.ok(data={"msg": res_msg})


@router.post("/img")
async def create_img_msg(user_id: int = Form(...), file: UploadFile = File(...),
                         authorization: Union[str, None] = Header(None)):
    my_id = my_jwt.get_user_id(authorization)
    url = file_util.save2local(file.file.read(), file.filename)
    db_message = DB_PrivateMessage(sender_id=my_id, rcver_id=user_id, img=url)
    db_message.save()
    save_notification(my_id, user_id)
    res_msg = {
        "id": db_message.id,
        "createTime": datetime.now(),
        "text": db_message.text,
        "img": db_message.img,
        "senderId": my_id,
    }
    return Response.ok(data={"msg": res_msg})


@router.get("/user/{user_id}")
async def get_msgs(user_id: int, authorization: Union[str, None] = Header(None)):
    my_id = my_jwt.get_user_id(authorization)
    msgs = DB_PrivateMessage.select().where(
        (DB_PrivateMessage.sender_id == my_id) & (DB_PrivateMessage.rcver_id == user_id) |
        (DB_PrivateMessage.sender_id == user_id) & (DB_PrivateMessage.rcver_id == my_id)
    )
    res_msgs = []
    for msg in msgs:
        res_msg = {
            "id": msg.id,
            "createTime": msg.create_time,
            "text": msg.text,
            "img": msg.img,
            "senderId": msg.sender_id,
        }
        res_msgs.append(res_msg)
        if msg.has_read is False:
            DB_PrivateMessage.update(has_read=True).where(
                DB_PrivateMessage.id == msg.id).execute()
    return Response.ok(data={"msgs": res_msgs})

# @router.get("/unread")
# async def get_unread_msgs(user_id: int, authorization: Union[str, None] = Header(None)):
#     my_id = my_jwt.get_user_id(authorization)
#     sql = DB_Promotion.select().where(DB_Promotion.user_id == user_id).order_by(DB_Promotion.create_time.desc())
#     prmotions = list(sql.dicts())
#     return Response.ok(data={"promotions": prmotions})
