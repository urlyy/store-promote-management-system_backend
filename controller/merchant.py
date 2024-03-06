from datetime import datetime
from typing import Union, List



from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.params import Form, Header
from PO.user import User as DB_User, ROLE_MERCHANT

from DO.response import Response
from utils import my_jwt, file_util
from PO.comment2merchant import Comment2Merchant as DB_Comment2Merchant
from PO.merchant_meta import MerchantMeta as DB_MerchantMeta,CATEGORIES
import recommend

router = APIRouter()



@router.post("")
async def be_merchant(latitude: float, longitude: float,
                      authorization: Union[str, None] = Header(None, convert_underscores=True)):
    my_id = my_jwt.get_user_id(authorization)
    DB_User.update(role=ROLE_MERCHANT).where(DB_User.id == my_id).execute()
    DB_MerchantMeta(user_id=my_id, location=[latitude, longitude], category=CATEGORIES[0]).save()
    recommend.retrain()
    return Response.ok(data={'category':CATEGORIES[0]})


@router.post("/location")
async def update_location(latitude: float, longitude: float,
                          authorization: Union[str, None] = Header(None, convert_underscores=True)):
    user_id = my_jwt.get_user_id(authorization)
    location = [round(latitude, 6), round(longitude, 6)]
    DB_MerchantMeta.update(location=location).where(DB_MerchantMeta.user_id == user_id).execute()
    return Response.ok()


@router.post("/{user_id}/comment")
async def create_comment(user_id: int, files: List[UploadFile] = [], text: str = Form(...), star: int = Form(...),
                         authorization: Union[str, None] = Header(None)):
    my_id = my_jwt.get_user_id(authorization)
    urls = []
    for file in files:
        url = file_util.save2local(file.file.read(), file.filename)
        urls.append(url)
    db_comment = DB_Comment2Merchant(user_id=my_id, merchant_id=user_id, text=text, imgs=urls, star=star)
    m = DB_MerchantMeta.select().where(DB_MerchantMeta.user_id == user_id).first()
    DB_MerchantMeta.update(comment_num=m.comment_num + 1).where(DB_MerchantMeta.id == m.id).execute()
    db_comment.save()
    comment = {
        'id':db_comment.id,
        'text':db_comment.text,
        'star':db_comment.star,
        'imgs':db_comment.imgs,
        'merchantId': db_comment.merchant_id,
        'createTime': datetime.now(),
        'userId':my_id
    }
    # save_notification(my_id,user_id)
    # msg = PrivateMessage.from_po(db_message)
    return Response.ok(data={"comment": comment})


@router.get("/{merchant_id}/comment")
async def get_comments2merchant(merchant_id: int, authorization: Union[str, None] = Header(None)):
    user_id = my_jwt.get_user_id(authorization)
    user_id_set = set()
    db_comments = DB_Comment2Merchant.select().where((DB_Comment2Merchant.merchant_id == merchant_id) & (DB_Comment2Merchant.status==1)).order_by(DB_Comment2Merchant.create_time.desc())
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
            'createTime': c.create_time,
            'text': c.text,
            'userId': u.id,
            'username': u.username,
            'star': c.star,
            'imgs': c.imgs,
            'avatar': u.avatar,
        }
        comments.append(comment)
    return Response.ok(data={"comments": comments})


@router.post("/category")
async def change_category(category: str, authorization: Union[str, None] = Header(None)):
    my_id = my_jwt.get_user_id(authorization)
    DB_MerchantMeta.update(category=category).where(DB_MerchantMeta.user_id == my_id).execute()
    return Response.ok()
