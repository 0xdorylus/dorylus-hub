from pydantic import BaseModel, Field
from beanie import Document, PydanticObjectId
from datetime import datetime

from agent.models.base import BaseDocument
from agent.utils.common import get_unique_id, get_current_time
from pydantic import BaseModel, Field

class Notice(BaseDocument):
    id:str=Field(default_factory=get_unique_id)
    uid: str
    kind: str
    content: str=""
    channel_id:str=""
    message: str=""
    sent:int=0
    create_at: int=get_current_time()
    update_at: int=get_current_time()

    class Settings:
        name = "notice"
    class Config:
        json_schema_extra = {
            "example": {


            }
        }