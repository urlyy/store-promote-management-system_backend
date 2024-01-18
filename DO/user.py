import jsonpickle

from PO.user import User as DB_User

class User:
    id: int
    username: str
    coin: int
    avatar: str
    brief: str
    role:int
    location:list[str]
    is_followed_by_me:bool

    def __init__(self, id, username, brief, avatar, coin,role,location,follow):
        self.id = id
        self.username = username
        self.brief = brief
        self.avatar = avatar
        self.coin = coin
        self.role = role
        self.location = location
        self.follow = follow

    @classmethod
    def from_po(cls, user: DB_User,follow=False):
        return cls(user.id, user.username, user.brief, user.avatar, user.coin,user.role,user.location,follow)

    # def __str__(self):
    #     return jsonpickle.encode(self,unpicklable=False)