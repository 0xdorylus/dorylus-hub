import logging

from bson import ObjectId, Decimal128
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Set
from ipaddress import IPv4Address

import pymongo
from beanie import Document, Indexed, before_event, after_event
import secrets
from beanie import Document, PydanticObjectId

from agent.models.base import BaseDocument
from agent.models.request_response_model import UserInfoModel
from agent.utils.common import get_unique_id, get_current_time, error_return

from agent.utils.common import success_return
from agent.utils.common import op_log
from agent.config import CONFIG


class Agent(BaseDocument):
    id: str = Field(default_factory=get_unique_id)
    uid: str
    username: str=""
    nickname:str=""
    avatar: Optional[str] = ""
    greeting: Optional[str] = ""
    temperature: Optional[float] = 0.5
    visiablity: Optional[int] = 1
    subscribed_num: Optional[int] = 0
    share_num: Optional[int] = 0
    user_prompt: Optional[str] = ""
    system_prompt: Optional[str] = ""
    background: Optional[str] = ""
    description: Optional[str] = ""
    intro: Optional[str] = ""
    banner: str = ""
    preview_list: List[str] = []

    main_model: Optional[str] = "Lama3-8B"
    user_tags: Optional[List] = []
    tag_ids: Optional[List] = []
    language: Optional[str] = "english"
    free_talk_num: Optional[int] = 100
    tool_ids: Optional[List] = []

    chat_num: Optional[int] = 0
    consumption:float=0 #消耗
    uv:int=0 #使用人数
    revenue:float=0 # 收入
    home_url:str=""
    access_url:str=""
    is_remote:bool=False
    create_at: int = get_current_time()
    update_at: int = get_current_time()

    class Settings:
        name = "agent"
        indexes = [
            [
                ("uid", pymongo.ASCENDING)
            ],
        ]

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_schema_extra = {
            "example": {

            }
        }




    def get_avatar(self):
        if self.avatar:
            return self.avatar
        else:
            return CONFIG.default_role_avatar

    @classmethod
    async def register_agent(cls,uid,username,intro,home_url,access_url,avatar):
        agent = await Agent.find_one({"username": username})
        if agent is not None:
            return error_return(1, "Username Exists")

        agent = await Agent(
            uid=uid,
            username=username,
            intro=intro,
            home_url=home_url,
            access_url=access_url,
            is_remote=True,
            avatar=avatar
        ).create()
        return success_return(agent)
    @classmethod
    async def get_name(cls, id):
        data = await cls.get(id)
        if data:
            return data.name
        else:
            return ""

    @classmethod
    async def subscribe_tool(cls, uid: str, agent_id: str, tool_id: str):
        await op_log("subscribe_tool uid %s %s ", uid, tool_id)
        filter = {
            Agent.uid == uid,
            Agent.id == agent_id
        }
        ret = await cls.find_one(filter).update({"$addToSet": {cls.tool_ids: tool_id}})
        logging.info(ret)

        return success_return(ret)

    @classmethod
    async def operate_counter(cls, agent_id: str, field: str, num: int):

        ret = await cls.find_one({"_id": agent_id}).update({"$inc": {field: num}})
        logging.info(ret)

        return success_return(ret)

    @classmethod
    async def unsubscribe_tool(cls, uid: str, agent_id: str, tool_id: str):
        await op_log("subscribe_tool uid %s %s ", uid, tool_id)
        filter = {
            "uid": uid,
            "_id": agent_id
        }
        ret = await cls.find_one(filter).update({"$pull": {cls.tool_ids: {"$in": [tool_id]}}})
        logging.info(ret)
        return True





class AgentOnboardTask(BaseDocument):
    """
    AgentOnboard 用户第一次注册时需要完成的任务

    比如：系统任务
    1）设置喜欢的语言
    2）设置昵称
    3）设置头像

    """
    id: str = Field(default_factory=get_unique_id)
    creator: str #谁创建的
    agent_id: str #谁创建的
    task_name:str
    task_kind:str
    task_content:str

