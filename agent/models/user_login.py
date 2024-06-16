import logging

from datetime import datetime
from typing import Optional, List

import pymongo

from beanie import Document, PydanticObjectId

from agent.models.base import BaseDocument
from agent.utils.common import get_unique_id, get_current_time
from pydantic import BaseModel, Field





class UserLogin(BaseDocument):
    """

    """
    id: str = Field(default_factory=get_unique_id)
    uid:str
    ymd:int
    num:int=1
    ip: str = ""
    create_at: int = get_current_time()

    class Settings:
        name = "user_login"
        indexes = [
            [
                ("uid", pymongo.ASCENDING),
                ("ymd", pymongo.ASCENDING),

            ],
        ]

