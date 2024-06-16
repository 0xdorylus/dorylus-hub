from typing import List, Optional

import pymongo
from fastapi import APIRouter, Depends, Response

from agent.models.agent import Agent
from agent.models.assistant import AssistantModel, Assistant, CreateAssistantModel
from agent.models.base import GenericResponseModel
from agent.models.request_response_model import GeneralRequestModel,CreateAgentModel
from agent.services.agent_service import AgentService
from agent.services.assistant_service import AssistantService
from agent.utils.x_auth import get_uid_by_token
from agent.models.subscribe import Subscription
router = APIRouter(prefix="/api", tags=["api"])

from pydantic import BaseModel, Field



@router.post("/create_agent", response_model=GenericResponseModel[str],summary="创建AI智能体")
async def create_agent(form: CreateAgentModel, uid: str = Depends(get_uid_by_token),
                           agent_service: AgentService = Depends()) :
    """Create Assistant
        创建角色 ，只需部分字段
    """
    agent_id = await agent_service.create_agent(uid, form)
    return GenericResponseModel(result=agent_id)

class AgentItemModel(BaseModel):
    uid: str
    name: str = ""
    nickname: str = ""
    avatar: Optional[str] = ""
    greeting: Optional[str] = ""
    temperature: Optional[float] = 1.0
    visiablity: Optional[int] = 1
    subscribed_num: Optional[int] = 0
    chat_num: Optional[int] = 0
    share_num: Optional[int] = 0
    prompt: Optional[str] = ""
    system_prompt: Optional[str] = ""
    background: Optional[str] = ""
    description: Optional[str] = ""
    intro: Optional[str] = ""
    banner: str = ""
    preview_list: List[str] = []

    main_model: Optional[str] = "gpt-3.5-turbo-16k-0613"
    user_tags: Optional[List] = []
    tag_ids: Optional[List] = []
    language: Optional[str] = "english"
    free_talk_num: Optional[int] = 10
    tool_ids: Optional[List] = []
    height: Optional[str] = ""
    mbti: Optional[str] = ""
    create_at: int

class AgentItemsResponseModel(BaseModel):
    total: int = 0
    total_page: int = 1
    list: List[AgentItemModel] = []
def callback_agent_list_item(item):
    return AgentItemModel(**item.dict())
@router.post("/my_agent_list", response_model=GenericResponseModel[AgentItemsResponseModel],summary="我创建AI智能体")
async def my_agent_list(request_form: GeneralRequestModel,uid: str = Depends(get_uid_by_token)) :
    query = {}
    if request_form.uid > 0:
        query = {"uid": request_form.uid}
    options = {
        "page": request_form.page,
        "pagesize": request_form.pagesize,
        "sort": [("_id", pymongo.DESCENDING)],
    }
    return await Agent.get_page(query=query, options=options, callback=callback_agent_list_item)


async def callback_subscribe_agent_list_item(item):
    target = item.target
    item = await Agent.get(target)
    return AgentItemModel(**item.model_dump())

@router.post("/my_subscribe_list", response_model=GenericResponseModel[List],summary="我订阅的AI智能体")
async def my_subscribe_list(request_form: GeneralRequestModel,uid: str = Depends(get_uid_by_token)) :
    query = {}
    if request_form.uid > 0:
        query = {"who":uid,"type":"agent"}
    options = {
        "page": request_form.page,
        "pagesize": request_form.pagesize,
        "sort": [("_id", pymongo.DESCENDING)],
    }
    return await Subscription.get_page(query=query, options=options, callback=callback_subscribe_agent_list_item, is_async_callback=True)
