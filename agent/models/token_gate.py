import logging

from bson import ObjectId
from pydantic import BaseModel, Field
from datetime import datetime
from ipaddress import IPv4Address
from typing import Optional, List, Set

import pymongo
from beanie import Document, Indexed, before_event, after_event

from agent.utils.common import get_unique_id, error_return, encode_input
from agent.utils.common import op_log
from agent.utils.common import success_return
from fastapi import Depends, HTTPException, status
from agent.models.request_response_model import UserInfoModel, UserDetailModel


class TokenGateItemModel(BaseModel):
    id: str = ""
    channel_id:str
    mainchain: str
    token: str
    contract: str
    num: float
    acl_type:str
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example":
                {"id":"","channel_id":"","mainchain": "BSC","token":"DSO","num":1,"acl_type":"token"}
        }


class TokenGate(Document):
    id: str = Field(default_factory=get_unique_id)
    uid: str=""
    token: str = ""
    mainchain: str = "BSC"
    contract:str=""
    num:float=0.0
    acl_type:str="ERC20" #NFT,PAY
    channel_id:str=""

    create_at: datetime = datetime.now()
    update_at: datetime = datetime.now()



    @classmethod
    async def get_acl_items(cls,id):
        outs: List[TokenGateItemModel] = []
        items = await cls.find(cls.channel_id==id).to_list()
        for item in items:
            data = TokenGateItemModel(**item.model_dump())
            outs.append(data)
        return outs

    class Settings:
        name = "token_gate"