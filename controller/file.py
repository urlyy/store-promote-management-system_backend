import uuid
from fastapi import APIRouter, UploadFile
from DO.response import Response
from utils import config, file_util
import os

router = APIRouter()


@router.post("")
def upload(file: UploadFile):
    url = file_util.save2local(file.file.read(), file.filename)
    return Response.ok({"file": url})
    # else:
    #     raise HTTPException(status_code=404, detail="Item not found")
    # 如果条件不满足，可以使用 HTTPException 抛出自定义状态码
