from PO.comment2merchant import Comment2Merchant as DB_Comment2Merchant
from PO.user import User as DB_User

class Comment2Merchant:
    id: int
    user_id: int
    username: str
    avatar: str
    text: str
    imgs:list
    create_time: str
    star:int

    def __init__(self, id,user_id,username,avatar, text,imgs,star, create_time):
        self.id = id
        self.username=username
        self.avatar= avatar
        self.text = text
        self.user_id = user_id
        self.imgs = imgs
        self.star = star
        self.create_time = create_time


    @classmethod
    def from_po(cls, c2m: DB_Comment2Merchant,user:DB_User):
        return cls(c2m.id, c2m.user_id, user.username,user.avatar,c2m.text,c2m.imgs,c2m.star,c2m.create_time)
