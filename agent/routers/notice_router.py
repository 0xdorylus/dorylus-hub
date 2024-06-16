from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel

from agent.models.assistant import AssistantModel, Assistant, CreateAssistantModel
from agent.models.base import GenericResponseModel
from agent.services.assistant_service import AssistantService
from agent.services.social_service import SocialService
from agent.utils.x_auth import get_uid_by_token

router = APIRouter(prefix="/notice", tags=["notice"])

class NoticeModel(BaseModel):
    uid:str
    content:str
    kind:str="text"

class NoticeChannelModel(BaseModel):
    channel_id:str
    uid:str
    content:str
    kind:str="text"


@router.post("/send",response_model=GenericResponseModel[bool])
async def send_notice(form:NoticeModel,social_service:SocialService=Depends()):
    """Get current user"""

    flag  = await social_service.send_notice(form.uid,form.content)
    return GenericResponseModel(result=flag)

@router.post("/send_to_channel",response_model=GenericResponseModel[bool])
async def send_to_channel(form:NoticeChannelModel,social_service:SocialService=Depends()):
    """Get current user"""

    flag  = await social_service.send_notice(form.uid,form.content)
    return GenericResponseModel(result=flag)



#
# @router.post("/me")
# async def send(askForm:AskForm):
#     """Get current user"""
#     return {"uid": uid}
#
# @router.post("/query"):
# async def query(assistant_id:str):
#     """Get current user"""
#
#     return {"uid": uid}


