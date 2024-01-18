from PO.private_message import PrivateMessage as DB_PrivateMessage


class PrivateMessage:
    id: int
    text: str
    img: str
    sender_id: int
    rcver_id: int
    create_time: int

    def __init__(self, id, text, img, sender_id, rcver_id, create_time):
        self.id = id
        self.text = text
        self.img = img
        self.sender_id = sender_id
        self.rcver_id = rcver_id
        self.create_time = create_time

    @classmethod
    def from_po(cls, pm: DB_PrivateMessage):
        print(pm)
        return cls(pm.id, pm.text, pm.img, pm.sender_id, pm.rcver_id, pm.create_time)
