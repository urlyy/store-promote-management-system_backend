from typing import Union, List

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.params import Form, Header, File
from PO.private_message import PrivateMessage as DB_PrivateMessage
from DO.private_message import PrivateMessage
from PO.notification import Notification as DB_Notification,TYPE_PRIVATE_MESSAGE
from PO.user import User as DB_User
from DO.response import Response
from utils import my_jwt, file_util

router = APIRouter()


def save_notification(my_id, user_id):
    noti = DB_Notification(rcver_id=user_id, text="给你发送了私信", param={"sender_id": my_id},type=TYPE_PRIVATE_MESSAGE)
    noti.save()

@router.post("/text")
async def create_text_msg(text: str = Form(...), user_id: int = Form(...),
                          authorization: Union[str, None] = Header(None)):
    my_id = my_jwt.get_user_id(authorization)
    db_message = DB_PrivateMessage(sender_id=my_id, rcver_id=user_id, text=text)
    db_message.save()
    save_notification(my_id,user_id)
    msg = PrivateMessage.from_po(db_message)
    return Response.ok(data={"msg": msg})


@router.post("/img")
async def create_img_msg(user_id: int = Form(...), file: UploadFile = File(...),
                         authorization: Union[str, None] = Header(None)):
    my_id = my_jwt.get_user_id(authorization)
    url = file_util.save2local(file.file.read(), file.filename)
    db_message = DB_PrivateMessage(sender_id=my_id, rcver_id=user_id, img=url)
    db_message.save()
    save_notification(my_id,user_id)
    msg = PrivateMessage.from_po(db_message)
    return Response.ok(data={"msg": msg})


@router.get("/user/{user_id}")
async def get_msgs(user_id: int, authorization: Union[str, None] = Header(None)):
    my_id = my_jwt.get_user_id(authorization)
    sql = DB_PrivateMessage.select().where(
        (DB_PrivateMessage.sender_id == my_id and DB_PrivateMessage.rcver_id == user_id) or (
                    DB_PrivateMessage.sender_id == user_id and DB_PrivateMessage.rcver_id == my_id))
    msgs = list(sql)
    res_msgs = []
    for msg in msgs:
        res_msg = PrivateMessage.from_po(msg)
        res_msgs.append(res_msg)
        if msg.has_read is False:
            DB_PrivateMessage.update(has_read=True).where(
                DB_PrivateMessage.sender_id == user_id and DB_PrivateMessage.rcver_id == my_id).execute()
    return Response.ok(data={"msgs": res_msgs})


@router.get("/unread")
async def get_unread_msgs(user_id: int, authorization: Union[str, None] = Header(None)):
    my_id = my_jwt.get_user_id(authorization)
    sql = DB_Promotion.select().where(DB_Promotion.user_id == user_id).order_by(DB_Promotion.create_time.desc())
    prmotions = list(sql.dicts())
    return Response.ok(data={"promotions": prmotions})
