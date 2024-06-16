import logging

from bson import ObjectId
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Set

from beanie import Document, Indexed, before_event, after_event

from agent.models.token_gate import TokenGate, TokenGateItemModel
from agent.utils.common import get_unique_id, error_return, encode_input

class Acl(Document):
    id: str = Field(default_factory=get_unique_id)
    target: str=""
    target_type:str="channel"
    acl_items:List[TokenGate]=[]

    create_at: datetime = datetime.now()
    update_at: datetime = datetime.now()


    @classmethod
    async def get_channel_acl(cls,target):
        data = await  cls.get(target)
        if data:
            return data.acl_items
        else:
            return None

    class Settings:
        name = "acl"