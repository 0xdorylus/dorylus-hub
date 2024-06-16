from typing import List, Optional

import pymongo
from fastapi import APIRouter, Depends, Response

from agent.models.agent import Agent
from agent.models.assistant import AssistantModel, Assistant, CreateAssistantModel
from agent.models.base import GenericResponseModel
from agent.models.request_response_model import GeneralRequestModel, CreateAgentModel, IDModel
from agent.services.agent_service import AgentService
from agent.services.assistant_service import AssistantService
from agent.utils.common import success_return, error_return
from agent.utils.x_auth import get_uid_by_token
from agent.models.subscribe import Subscription
router = APIRouter(prefix="/agent", tags=["agent"])

from pydantic import BaseModel, Field



@router.post("/create_agent", response_model=GenericResponseModel,summary="创建AI智能体")
async def create_agent(form: CreateAgentModel, uid: str = Depends(get_uid_by_token),
                           agent_service: AgentService = Depends()) :
    """Create Assistant
        创建角色 ，只需部分字段
    """
    agent_id = await agent_service.create_agent(uid, form)
    return GenericResponseModel(result=agent_id)

class AgentItemModel(BaseModel):
    id:str
    uid: str
    username: str = ""
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
    intro: Optional[str] = ""
    banner: str = ""
    preview_list: List[str] = []
    tag_list:List[str] = []

    main_model: Optional[str] = "Lama3-8B"
    user_tags: Optional[List] = []
    tag_ids: Optional[List] = []
    language: Optional[str] = "english"
    free_talk_num: Optional[int] = 10
    tool_ids: Optional[List] = []
    height: Optional[str] = ""
    mbti: Optional[str] = ""
    create_at: int

    consumption:float=0 #消耗
    uv:int=0 #使用人数
    revenue:float=0
    is_remote:bool=False



class AgentItemsResponseModel(BaseModel):
    total: int = 0
    total_page: int = 1
    list: List[AgentItemModel] = []
def callback_agent_list_item(item):
    return AgentItemModel(**item.dict())
@router.post("/my_agent_list", response_model=GenericResponseModel[AgentItemsResponseModel],summary="我创建AI智能体")
async def my_agent_list(request_form: GeneralRequestModel,uid: str = Depends(get_uid_by_token)) :
    query = {}
    # if request_form.uid > 0:
    query = {"uid": uid}
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

@router.post("/agent_list", response_model=GenericResponseModel[AgentItemsResponseModel],summary="智能体列表")
async def agent_list(request_form: GeneralRequestModel) :
    query = {
        "visiablity":1
    }


    options = {
        "page": request_form.page,
        "pagesize": request_form.pagesize,
        "sort": [("_id", pymongo.DESCENDING)],
    }
    return await Agent.get_page(query=query, options=options, callback=callback_agent_list_item)


@router.post("/detail", response_model=GenericResponseModel,summary="智能体详情")
async def agent_detail(form:IDModel,uid: str = Depends(get_uid_by_token)):
    query = {
        "_id":form.id,
        "uid":uid
    }
    agent = await Agent.find_one(query)
    if agent is not None:
        return success_return(agent)
    else:
        return error_return(404,"Not Found")



class AgentBaseModel(BaseModel):
    id:str
    username:str
    avatar:str
    intro:str

@router.post("/save_base", response_model=GenericResponseModel,summary="智能体详情")
async def save_base(form:AgentBaseModel,uid: str = Depends(get_uid_by_token)):
    query = {
        "_id":form.id,
        "uid":uid
    }
    agent = await Agent.find_one(query)
    agent2 = await Agent.find_one({"username":form.username})
    if agent2 is not None and agent is not None:
        if agent2.uid != uid:
            return error_return(1, "Username Exists")
    if agent is None:
        return error_return(404, "Not Found")
    await Agent.find_one(query).update_one({"$set":form.model_dump()})
    return success_return(agent)



class AgentLLMModel(BaseModel):
    id:str
    main_model:str
    temperature:float
    user_prompt:str
@router.post("/save_llm", response_model=GenericResponseModel,summary="智能体")
async def save_llm(form:AgentLLMModel,uid: str = Depends(get_uid_by_token)):
    query = {
        "_id":form.id,
        "uid":uid
    }
    agent = await Agent.find_one(query)
 
    if agent is None:
        return error_return(404, "Not Found")
    await Agent.find_one(query).update_one({"$set":form.model_dump()})
    return success_return(agent)


class RegisterAgentModel(BaseModel):
    username:str
    intro:str
    home_url:str=""
    access_url:str=""
    avatar:str=""

@router.post("/register_agent", response_model=GenericResponseModel, summary="register_agent")
async def register_agent(form: RegisterAgentModel, uid: str = Depends(get_uid_by_token)):
    return await Agent.register_agent(uid,form.username,form.intro,form.home_url,form.access_url,form.avatar)


class KnowledgeUrlModel(BaseModel):
    id:str
    urls:List[str]


@router.post("/deal_kb_url", response_model=GenericResponseModel, summary="处理知识库文件")
async def deal_kb_url(form: KnowledgeUrlModel, uid: str = Depends(get_uid_by_token)):
    return success_return(form)


