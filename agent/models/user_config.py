import logging


from datetime import datetime
from typing import Optional, List

import pymongo

from beanie import Document, PydanticObjectId
from agent.utils.common import get_unique_id, get_current_time
from pydantic import BaseModel, Field

class UserConfig(Document):
    id: str = Field(default_factory=get_unique_id)
    uid: str
    target:str=""
    key:str
    value:str
    create_at:datetime=datetime.now()
    update_at:datetime=datetime.now()

    @classmethod
    async def set_hot_model(cls,uid:str,hot:str):
        item = await cls.find_one({"uid":uid,"key":"hot_model"})
        if item:
            item.value = hot
            item.update_at = get_current_time()
            await item.save()
        else:
            doc = {"uid":uid,"key":"hot_model","value":hot}
            await cls(**doc).create()
    @classmethod
    async def get_hot_model(cls,uid:str):
        item = await cls.find_one({"uid":uid,"key":"hot_model"})
        if item:
            return item.value
        else:
            return ""

    @classmethod
    async def get_config(cls,uid:str,key:str):
        item = await cls.find_one({"uid":uid,"key":key})
        if item:
            return item.value
        else:
            return ""
    @classmethod
    async def get_girl_level(cls,uid:str,target:str):
        item = await cls.find_one({"uid":uid,"target":target})
        if item:
            return item.value
        else:
            return "1"
