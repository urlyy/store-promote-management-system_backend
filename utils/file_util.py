import os
import uuid
from utils import config


def save2local(bytes,filename)->str:
    # 生成随机新文件名
    file_name, file_extension = os.path.splitext(filename)
    new_uuid = str(uuid.uuid4())
    new_filename = f"{new_uuid}{file_extension}"
    static_dir = config.get('server.static_dir')
    relative_path = os.path.join(static_dir, new_filename)
    # 将文件写入本地
    with open(os.path.join(os.getcwd(), relative_path), "wb") as new_file:
        new_file.write(bytes)
    url = f"http://{config.get('server.host')}:{config.get('server.port')}/{static_dir}/{new_filename}"
    return url