import logging

from bson import ObjectId
from pydantic import BaseModel, Field
from datetime import datetime
from ipaddress import IPv4Address
from typing import Optional, List, Set, Annotated

import pymongo
from beanie import Document, Indexed, before_event, after_event, DecimalAnnotation

from agent.utils.common import get_unique_id, error_return, encode_input
from agent.utils.common import op_log
from agent.utils.common import success_return
from fastapi import Depends, HTTPException, status
from agent.models.request_response_model import UserInfoModel, UserDetailModel


class UserInvest(Document):
    id: str = Field(default_factory=get_unique_id)
    uid: str=""
    amount: Annotated[DecimalAnnotation, Field("0.000000")]
    hash: str =  Field("")
    status: int = 0
    create_at: datetime = datetime.now()
    update_at: datetime = datetime.now()
    class Settings:
        name = "user_invest"

    @classmethod
    async def submit_hash(cls,uid:str,hash:str)->bool:
        user_invest = await cls.find_one({"hash":hash})
        if user_invest:
            return False
        else:
            await UserInvest(uid=uid,hash=hash).insert()

            return True