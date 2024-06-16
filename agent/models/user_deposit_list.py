import logging

from bson import ObjectId, Decimal128
from pydantic import BaseModel, Field, Json
from datetime import datetime
from typing import Optional, Annotated
from ipaddress import IPv4Address
from decimal import Decimal
from agent.connection import get_next_id

import pymongo
from beanie import Document, Indexed, before_event, after_event, DecimalAnnotation
import secrets
from beanie import Document, PydanticObjectId
from beanie import Insert

from agent.utils.common import get_unique_id

from eth_account import Account


class UserDepositListModel(BaseModel):
    hash: Indexed(str, unique=True)
    status: int = 0
    deposit_id: int = 0
    amount: float = 0.0
    token: str = ""
    src: str = ""
    dst: str = ""
    uid: str = ""
    create_at: datetime


class UserDepositList(Document):
    id: str = Field(default_factory=get_unique_id)
    deposit_id: int
    uid: str
    hash: Indexed(str, unique=True)
    status: int = 0
    amount:  DecimalAnnotation = Field(decimal_places=8, default=0 )
    token: str = ""
    src: str = ""
    dst: Indexed(str, unique=False)
    update_at: datetime = datetime.now()
    create_at: datetime = datetime.now()

    class Settings:
        name = "user_deposit_list"
        indexes = [
            [
                ("uid", pymongo.ASCENDING)
            ],
        ]
    @classmethod
    async def save_tx(cls,uid,txhash,amount,token,src,address,status):

        # UserDepositList.get_settings().motor_collection.create_index("hash", unique=True)
        doc = {
            "deposit_id": await get_next_id("deposit"),
            "uid": uid,
            "hash": txhash,
            "status": status,
            "amount": amount,
            "token": token,
            "src": src,
            "dst": address
        }
        await UserDepositList(**doc).create()

    @classmethod
    async def get_total(cls,where={}):
        pipeline = [
            {"$match": where},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]
        result = await cls.aggregate(pipeline).to_list()
        # print
        total_amount = result[0]["total"]
        return total_amount

