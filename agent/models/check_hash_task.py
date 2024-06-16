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


class CheckHashTask(Document):
    hash: str
    num: int=10
    create_at: int = Field(default_factory=get_current_time)
    update_at: int = Field(default_factory=get_current_time)

    class Settings:
        name = "check_hash_task"
        indexes = [
            [
                ("hash", pymongo.ASCENDING)
            ],
        ]

    @classmethod
    async def get_hash_list(cls):
        return await cls.find({"num": {"$gt":0}}).to_list()

    @classmethod
    async def set_hash(cls,hash,num):
        vo = await cls.find_one({"hash": hash})
        if vo is None:
            doc = {
                "hash":hash,
                "num":num
            }
            await cls(**doc).create()
