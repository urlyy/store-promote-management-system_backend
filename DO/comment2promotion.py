from PO.comment2promotion import Comment2Promotion as DB_Comment2Promotion


class Comment2Promotion:
    id: int
    text: str
    user_id: int
    create_time: int

    def __init__(self, id, text, user_id, create_time):
        self.id = id
        self.text = text
        self.user_id = user_id
        self.create_time = create_time

    @classmethod
    def from_po(cls, c2p: DB_Comment2Promotion):
        return cls(c2p.id, c2p.text, c2p.user_id,  c2p.create_time)
