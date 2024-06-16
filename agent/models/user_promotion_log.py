import logging


from datetime import datetime
from typing import Optional, List

import pymongo

from beanie import Document, PydanticObjectId
from agent.utils.common import get_unique_id
from pydantic import BaseModel, Field

class UserPromotionLog(Document):
    id:str=Field(default_factory=get_unique_id)
    uid: str
    op_type: str = ""
    desc: str = ""
    create_at: datetime = datetime.now()

    @classmethod
    async def recoard(cls,uid,op_type,desc):
        doc = {
            "uid":uid,
            "op_type":op_type,
            "desc":desc
        }
        await cls(**doc).create()
    class Settings:
        name = "user_promotion_log"
        indexes = [
            [
                ("uid", pymongo.ASCENDING),
            ],
        ]
    class Config:
        json_schema_extra = {
            "example": {
                "uid": "1",
                "username": "bots001",
                "address": "0xE91C299427D5DB24Dcc064db3Dc42d1bF1bf187E",
                "date": datetime.now()
            }
        }