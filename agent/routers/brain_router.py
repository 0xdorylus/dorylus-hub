from fastapi import APIRouter, Depends, Response

from agent.models.assistant import AssistantModel, Assistant, CreateAssistantModel
from agent.models.base import GenericResponseModel
from agent.models.knowledge import TrainFileDataModel
from agent.models.request_response_model import UploadResponseModel
from agent.services.assistant_service import AssistantService
from agent.services.fs_service import FsService
from agent.utils.x_auth import get_uid_by_token
from agent.models.subscribe import Subscription
router = APIRouter(prefix="/brain", tags=["brain"])




@router.post("/knowoledge_upload", response_model=GenericResponseModel[UploadResponseModel],summary="上传角色私有知识库文件")
async def private_upload_file(form:TrainFileDataModel,
                              uid:str = Depends(get_uid_by_token),
                             file_service: FsService = Depends()):
    """
        上传图片/文件 私有的,私有上传的要用下面的下载接口下载
    """
    file = form.file
    is_private = True
    data =  await file_service.deal_file(uid,file,is_private)
    return GenericResponseModel()

