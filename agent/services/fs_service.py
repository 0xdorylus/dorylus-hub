from datetime import datetime

from dotenv import load_dotenv
from fastapi import UploadFile, HTTPException
from pathlib import Path

from agent.errors.biz import UserUploadError
from agent.models.base import GenericResponseModel
from agent.models.file_meta import FileMetadata
# SoldityFileMeta
import tempfile
import shutil
import os

from agent.models.request_response_model import UploadResponseModel
from agent.utils import fshelper

load_dotenv()
import os
from agent.config import CONFIG

class FsService:
    file_domain=""
    def __init__(self):
        self.file_domain = os.getenv("FILE_DOMAIN")

    async def get_file(self, id: str):
        file = await FileMetadata.get(id)
        if file is None:
            return None
        else:
            return file.filepath
    async def deal_file(self,uid:int, file: UploadFile,is_private:bool=False)->UploadResponseModel:
        if not file:
            raise HTTPException(403,"file is empty")
        else:
            file_ext = os.path.splitext(file.filename)[1].lower()
            file_meta = await FileMetadata(
                filename=file.filename,
                content_type=file.content_type,
                file_ext=file_ext,
                uid=uid,
            ).create()
            id = str(file_meta.id)
            # 获取当前日期并创建目录
            current_date = datetime.now().strftime("%Y-%m-%d")
            dst_dir  = CONFIG.fs_store_dir+current_date
            # print(dst_dir)
            if not os.path.exists(dst_dir):
                os.makedirs(dst_dir)
            file_path = os.path.join(current_date, id + file_ext)
            # print(self.file_domain)
            dst_file_path = os.path.join(dst_dir, id + file_ext)
            # print(dst_file_path)

            path = Path(dst_file_path)
            file_size = path.write_bytes(await file.read())

            file_meta.filepath = dst_file_path
            file_meta.size = file_size
            file_meta.status = 1
            file_meta.filehash = await fshelper.get_file_hash(dst_file_path)
            await file_meta.save()
            url = self.file_domain + file_path
            if is_private:
                data = {
                    "id":file_meta.id,
                    "size":file_size,
                    "url": url,
                    "filename": file.filename,
                    "content_type": file.content_type,
                }
            else:
                data = {
                    "url":url,
                    "size":file_size,
                    "filename":file.filename,
                    "content_type":file.content_type,

                }

            return UploadResponseModel(**data)
