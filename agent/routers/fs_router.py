import logging
import os
from typing import Optional

from fastapi import APIRouter, HTTPException

from agent.models.base import GenericResponseModel

from fastapi import Depends

from fastapi import FastAPI, File, UploadFile,Request
from fastapi.responses import FileResponse

from agent.models.channel import ChannelFile, Channel
from agent.models.request_response_model import UploadResponseModel, IDModel
from agent.utils.common import success_return
from agent.utils.x_auth import get_uid_by_token

router = APIRouter()


from agent.models.file_meta import FileMetadata
from agent.services.fs_service import FsService

ALLOWED_FILE_EXTENSIONS = [".pdf",".txt",".md",".csv"]


def allowed_file(filename: str) -> bool:
    ext = os.path.splitext(filename)[1]
    return ext.lower() in ALLOWED_FILE_EXTENSIONS



@router.post("/upload", response_model=GenericResponseModel[UploadResponseModel],tags=["fs"],summary="上传文件")
async def create_upload_file(uid:str = Depends(get_uid_by_token),
                             file: UploadFile = File(...),
                             file_service: FsService = Depends()):
    """
        上传图片/文件 可共享的

    """

    data = await file_service.deal_file(uid,file)
    return GenericResponseModel(result=data)

@router.post("/private_upload", response_model=GenericResponseModel[UploadResponseModel],tags=["fs"],summary="上传私有文件")
async def private_upload_file(uid:str = Depends(get_uid_by_token),
                             file: UploadFile = File(...),
                             file_service: FsService = Depends()):
    """
        上传图片/文件 私有的,私有上传的要用下面的下载接口下载
    """
    is_private = True
    data =  await file_service.deal_file(uid,file,is_private)
    return GenericResponseModel(result=data)

#
#
@router.get("/download/{file_id}",tags=["fs"])
async def download_file(file_id:str,uid:str = Depends(get_uid_by_token),summary="下载文件"):
    """
    根据ID下载图片
    """
    file = await FileMetadata.get(file_id)
    if file is None:
        raise HTTPException(404, "Not Found")

    elif file.uid != uid:
        raise HTTPException(403,"Forbidden")
    else:
        if os.path.isfile(file.filepath):
            return FileResponse(file.filepath, filename=file.filename)
        else:
            raise HTTPException(404, "Not Found")

from pydantic import BaseModel
class AddChannelFileModel(BaseModel):
    channel_id:str
    filename:str
    url:str
    size:int
    uid:Optional[str]=""
    content_type:str=""

@router.post("/add_channel_file", response_model=GenericResponseModel,tags=["fs"],summary="给频道增加文件")
async def add_channel_file(form:AddChannelFileModel,uid:str = Depends(get_uid_by_token)):
    form.uid = uid
    flag = await Channel.is_user_in_admin(uid,form.channel_id)
    if flag:
        file = await ChannelFile(**form.model_dump()).create()
        return GenericResponseModel(result=file)
    else:
        raise HTTPException(403,"Forbidden")



@router.post("/channel_files", response_model=GenericResponseModel,tags=["fs"],summary="文件列表")
async def channel_files(form:IDModel,uid:str = Depends(get_uid_by_token)):
    flag = await Channel.is_user_in_channel(uid,form.id)
    if flag:
        items = await ChannelFile.find({"channel_id":form.id}).to_list()
        return GenericResponseModel(result=items)
    else:
        return GenericResponseModel(result=[])
