from typing import List

from fastapi import APIRouter, Depends, Response, HTTPException

from agent.models.base import GenericResponseModel
from agent.models.channel import Channel
from agent.models.onboard_task import TaskBox
from agent.models.request_response_model import FinishResponseModel, IDModel
from agent.models.token_gate import TokenGateItemModel, TokenGate
from agent.utils.x_auth import get_uid_by_token
from pydantic import BaseModel, Field

router = APIRouter(prefix="/onboard", tags=["onboard"])





class ChannelOnboardTaskModel(BaseModel):
    name:str=Field(...,description="任务名称")
    desc:str=Field(...,description="任务描述")
    target:str=Field(...,description="频道ID")



@router.post("/create_channel_onboard_task", response_model=GenericResponseModel[str], summary="配置频道")
async def create_channel_onboard_task(form: ChannelOnboardTaskModel, uid: str = Depends(get_uid_by_token)):
    """

    """
    channel = await Channel.get(form.channel_id)
    if channel.uid != uid and uid not in channel.admin_ids:
        raise HTTPException(status_code=403, detail="没有权限")

    items = form.model_dump()
    items['creator'] = uid
    items['tag'] = "channel"

    task = await TaskBox(**items).create()
    return GenericResponseModel(result=task.id)



@router.post("/del_group_acl_item", response_model=GenericResponseModel, summary="删除一条权限")
async def del_group_acl_item(form:IDModel, uid: str = Depends(get_uid_by_token)):
    """
        删除一条权限
    """

    r = await TokenGate.find_one(TokenGate.id==form.id,TokenGate.uid==uid).delete_one()
    if r.deleted_count==1:
        return GenericResponseModel()
    else:
        return GenericResponseModel(code=301,message="not_modified")

@router.post("/list_group_acl_item", response_model=GenericResponseModel[List[TokenGateItemModel]], summary="群权限列表")
async def list_group_acl_item(form:IDModel):
    """
        群权限列表
    """
    data =  await TokenGate.get_acl_items(form.id)
    return GenericResponseModel(result=data)



