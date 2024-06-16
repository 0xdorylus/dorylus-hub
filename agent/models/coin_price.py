from beanie import Document
import logging

from bson import ObjectId, Decimal128
from pydantic import BaseModel, Field, Json
from datetime import datetime
from typing import Optional
from ipaddress import IPv4Address
from decimal import Decimal

import pymongo
from beanie import Document, Indexed, before_event, after_event
import secrets
from beanie import Document, PydanticObjectId
from beanie import Insert

from agent.utils.common import get_unique_id, get_current_time


class CoinPrice(Document):
    id: str = Field(default_factory=get_unique_id)
    token: str
    price: float
    create_at: int = Field(default_factory=get_current_time)
    update_at: int = Field(default_factory=get_current_time)


    class Settings:
        name = "coin_price"
        indexes = [
            [
                ("token", pymongo.ASCENDING)
            ],
        ]

    @classmethod
    async def get_price(cls,token):
        block = await cls.find_one({"token":token})
        if block:
            return block.price
        else:

            return None

    @classmethod
    async def set_price(cls,token,price):
        item = await cls.find_one({"token": token})
        if item is None:
            doc = {
                "token":token,
                "price":price
            }
            await cls(**doc).create()

        await cls.find_one({"token": token}).update({"$set":{"price":price,"update_at":datetime.now()}})