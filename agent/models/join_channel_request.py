import json
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field
from beanie import Document
from agent.utils.common import get_unique_id

class JoinChannelRequest(Document):
    id:str=Field(default_factory=get_unique_id)
    uid:str
    channel_id:str
    memo: str
    status: str
    create_at: datetime = datetime.now()
    update_at: datetime = datetime.now()

    class Settings:
        name = "join_channel_request"

    class Config:
        json_schema_extra = {
            "example": {


            }
        }
