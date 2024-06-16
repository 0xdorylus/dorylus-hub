import logging

from bson import ObjectId, Decimal128
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from ipaddress import IPv4Address

import pymongo
from beanie import Document, Indexed, before_event,after_event
import secrets
from beanie import Document, PydanticObjectId
from beanie import Insert

from agent.models.agent import Agent
from agent.models.assistant import Assistant, AssistantDetailModel
from agent.models.base import BaseDocument
from agent.utils.common import get_unique_id

from agent.utils.common import success_return
from agent.utils.common import op_log
from agent.utils.common import get_current_time

class SubscribeAssistantModel(BaseModel):
    assistant_id:str

class Subscription(BaseDocument):
    id: str = Field(default_factory=get_unique_id)
    who: str
    target: str
    type: str
    create_at: int=get_current_time()

    class Settings:
        name = "subscription"
        indexes = [
            "idx_who_target_type",
            [
                ("who", pymongo.ASCENDING),
                ("target", pymongo.DESCENDING),
                ("type", pymongo.DESCENDING),
            ],
        ]


    class Config:
        json_schema_extra = {
            "example": {
                "who": "bots001",
                "target": "0xE91C299427D5DB24Dcc064db3Dc42d1bF1bf187E",
                "type": "tool",

            }
        }

    @classmethod
    async def is_subscribed_assistant(cls, uid: str, assistant_id: str):
        vo = await cls.find_one(cls.who == uid, cls.target == assistant_id, cls.type == "assistant")
        if vo:
            return True
        else:
            return False

    @classmethod
    async def subscribe_agent(cls, uid:str, agent_id:str):
        vo = await cls.find_one(cls.who==uid,cls.target==agent_id,cls.type == "agent")
        await op_log("subscribe_agent uid %s %s ",uid,agent_id)
        if vo:
            logging.info("already subscribed %s",agent_id)
            return success_return(vo)
        else:
            data = {
                "who":uid,
                "target":agent_id,
                "type":"agent"
            }
            await Subscription(**data).create()
            await Agent.find_one(Agent.id == agent_id).update({"$inc":{"subscribed_num":1}})
            return success_return(vo)

    @classmethod
    async def unsubscribe_assistant(cls,uid:str,assistant_id:str):
        await op_log("unsubscribe_assistant uid %s %s ",uid,assistant_id)
        vo = await cls.find_one(cls.who==uid,cls.target==assistant_id,cls.type == "assistant").delete()
        Assistant.find_one(Assistant.id == assistant_id).update({"$inc": {"subscribed_num": -1}})

        return success_return(vo)

    @classmethod
    async def subscribe_tool(cls,assistant_id:str,tool_id:str):
        vo = await cls.find_one(cls.who==assistant_id,cls.target==assistant_id,cls.type == "tool")
        await op_log("subscribe_tool assistant_id %s %s ",assistant_id,tool_id)
        if vo:
            return success_return(vo)
        else:
            data = {
                "who":assistant_id,
                "target":tool_id,
                "type":"assistant"
            }
            await Subscription(**data).create()
            return success_return(vo)

    @classmethod
    async def unsubscribe_tool(cls,assistant_id:str,tool_id:str):
        await op_log("unsubscribe_tool assistant_id %s %s ",assistant_id,tool_id)
        vo = await cls.delete(cls.who==assistant_id,cls.target==tool_id,cls.type == "tool")
        return success_return(vo)

