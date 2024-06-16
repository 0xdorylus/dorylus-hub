import logging

import pymongo
from beanie import Document
from fastapi import HTTPException
from pydantic import Field

from agent.config import CONFIG
from agent.models.base import BaseDocument
from agent.utils.common import get_unique_id, get_current_time

from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Set

class ChanndelItemModel(BaseModel):
    id:str
    uid:str
    user_ids: List[str]=[]
    type:str
    category:Optional[str]=""
    name:str
    intro:str
    logo:str
    banner:str
    admin_ids: List[str]=[]
    tag_ids: List[str]=[]
    is_public:bool=False
    link:str=""

class UserChannel(BaseDocument):
    """
        用于存储用户创建的频道
        点对点和群聊都可以
    """
    id:str=Field(default_factory=get_unique_id)
    uid:str
    channel_id:str



    join_at: int = Field(default_factory=get_current_time) #用户进入
    update_at: int = Field(default_factory=get_current_time)


    class Settings:
        name = "user_channel"

        indexes = [
            "idx_who_target_type",
            [
                ("uid", pymongo.ASCENDING),
                ("channel_id", pymongo.DESCENDING),
            ],
        ]

    class Config:
        json_schema_extra = {
            "example": {
                "title": "tag",
                "value": "name",
            }
        }


    @classmethod
    async def is_first_join(cls,uid,channel_id):
        """
            判断是否是第一次加入
        """
        count=await cls.count({"uid":uid,"channel_id":channel_id})
        if count==0:
            return True
        else:
            return False