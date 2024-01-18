from fastapi import APIRouter, HTTPException
from fastapi.params import Form
from PO.user import User as DB_User, ROLE_ADMIN
from DO.user import User
from DO.response import Response
from utils import my_jwt

from PO.user import User as DB_User
from PO.promotion import Promotion as DB_Promotion
from PO.comment2merchant import Comment2Merchant as DB_Comment2Merchant
from PO.comment2promotion import Comment2Promotion as DB_Comment2Promotion

router = APIRouter()


@router.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    db_admin = DB_User.select().where((DB_User.username == username) & (DB_User.role == ROLE_ADMIN)).first()
    if db_admin is None:
        raise HTTPException(status_code=400, detail="不存在该用户")
    token = my_jwt.create_jwt(db_admin.id)
    user = User.from_po(db_admin)
    return Response.ok({"user": user, "token": token})

@router.get("/users")
async def get_users(role: int):
    sql = DB_User.select()
    if role!=None:
        sql = sql.where(DB_User.role == role)
    users = list(sql.dicts())
    return Response.ok({"users": users})

@router.get("/promotions")
async def get_promotions():
    sql = DB_Promotion.select()
    promotions = list(sql.dicts())
    return Response.ok({"promotions": promotions})

@router.get("/comments/promotion")
async def get_comments2promotion():
    sql = DB_Comment2Promotion.select()
    comments = list(sql.dicts())
    return Response.ok({"comments": comments})


@router.get("/comments/merchant")
async def get_comments2merchant():
    sql = DB_Comment2Merchant.select()
    comments = list(sql.dicts())
    return Response.ok({"comments": comments})
