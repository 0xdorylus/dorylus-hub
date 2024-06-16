import logging


from datetime import datetime
from typing import Optional, List

import pymongo

from beanie import Document, PydanticObjectId, DecimalAnnotation
from agent.utils.common import get_unique_id
from pydantic import BaseModel, Field

class UserAssetList(Document):
    id:str=Field(default_factory=get_unique_id)
    uid: str=""
    mainchain: str=""
    token: str=""
    amount:  DecimalAnnotation = Field(decimal_places=8, default=0 )
    op_type: str = ""
    desc: str = ""
    status:str ="unconfirmed"
    create_at: datetime = datetime.now()

    class Settings:
        name = "user_asset_list"
        indexes = [
            [
                ("uid", pymongo.ASCENDING),
                ("op_type", pymongo.ASCENDING)
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