from typing import Union, List

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.params import Form, Header
from PO.user import User as DB_User, ROLE_MERCHANT
from DO.user import User
from DO.response import Response
from utils import my_jwt, file_util
from PO.comment2merchant import Comment2Merchant as DB_Comment2Merchant
from DO.comment2merchant import Comment2Merchant
router = APIRouter()


@router.post("")
async def be_merchant(authorization: Union[str, None] = Header(None, convert_underscores=True)):
    user_id = my_jwt.get_user_id(authorization)
    DB_User.update(role=ROLE_MERCHANT).where(DB_User.id == user_id).execute()
    return Response.ok()


@router.post("/{user_id}/comment")
async def create_comment(user_id: int, files: List[UploadFile] = [], text: str = Form(...), star: int = Form(...),
                         authorization: Union[str, None] = Header(None)):
    print(text, star)
    print(user_id)
    print(len(files))
    my_id = my_jwt.get_user_id(authorization)
    urls = []
    for file in files:
        url = file_util.save2local(file.file.read(), file.filename)
        urls.append(url)
    db_comment = DB_Comment2Merchant(user_id=my_id, merchant_id=user_id, text=text, imgs=urls, star=star)
    db_comment.save()
    # save_notification(my_id,user_id)
    # msg = PrivateMessage.from_po(db_message)
    return Response.ok(data={"comment": db_comment.__data__})


@router.get("/{merchant_id}/comment")
async def get_comment2merchant(merchant_id: int, authorization: Union[str, None] = Header(None)):
    user_id = my_jwt.get_user_id(authorization)
    sql = DB_Comment2Merchant.select().where(DB_Comment2Merchant.merchant_id == merchant_id)
    db_comments = list(sql)
    user_id_set = set()
    for c in db_comments:
        user_id_set.add(c.user_id)
    user_dict = {}
    for id in user_id_set:
        user = DB_User.select().where(DB_User.id==id).first()
        user_dict[id] = user
    comments = []
    for c in db_comments:
        comment = Comment2Merchant.from_po(c,user_dict[c.user_id])
        comments.append(comment)
    return Response.ok(data={"comments": comments})
