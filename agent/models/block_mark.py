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


class BlockMark(Document):
    mainchain: str
    height: int
    create_at: int = Field(default_factory=get_current_time)
    update_at: int = Field(default_factory=get_current_time)


    class Settings:
        name = "block_mark"
        indexes = [
            [
                ("uid", pymongo.ASCENDING)
            ],
        ]

    @classmethod
    async def get_height(cls,mainchain,height=0):
        block = await cls.find_one({"mainchain":mainchain})
        if block:
            return block.height
        else:
            doc = {
                "mainchain": mainchain,
                "height":height
            }
            await cls(**doc).create()
            return height

    @classmethod
    async def set_height(cls,mainchain,height):
        # print("set_height:",mainchain,height)
        await cls.find_one({"mainchain": mainchain}).update({"$set":{"height":height}})