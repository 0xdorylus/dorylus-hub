from datetime import datetime
from typing import List

import pymongo
from beanie import Document
from bson import ObjectId
from agent.utils.common import get_unique_id
from pydantic import BaseModel, Field, EmailStr


class FeedbackIdModel(BaseModel):
    id:str

class FeedbackRequestModel(BaseModel):
    email: str=Field(...,min_length=1,max_length=128)
    content:str=Field(...,min_length=1,max_length=1000)

class FeedbackItemModel(BaseModel):
    id: str
    email: str
    content:str
    create_at: datetime
FeedbackItemModel.__annotations__ = {
    "id": str,
    "email": str,
    "content": str,
    "create_at": datetime
}

class FeedbackListModel(BaseModel):
    total:int=0
    total_page:int=1
    list:List[FeedbackItemModel]=[]

class Feedback(Document):
    id: str = Field(default_factory=get_unique_id)
    uid: str
    email: str
    content:str
    create_at: datetime = datetime.now()
    update_at: datetime = datetime.now()
    class Settings:
        name = "feedback"