import logging
from datetime import datetime
from typing import Annotated

import pymongo
from beanie import Document, Indexed, before_event,after_event
import secrets
from beanie import Document, PydanticObjectId
from beanie import Insert

from pydantic import BaseModel, Field
from agent.utils.common import get_unique_id

class  BizLoginModel(BaseModel):
    username: str
    password: str
    code: str=Field("",description="GA Code")
    sid:str=""


class BizUserModel(BaseModel):
    username: str=""
    password: str=""
    ga: str=""
    avatar: str=""

class BizUser(Document):
    id:str=Field(default_factory=get_unique_id)
    username: Indexed(str, unique=True)
    password: str=""
    ga: str=""
    avatar: str=""
    status:int=1
    create_at: datetime = datetime.now()
    update_at: datetime = datetime.now()

    class Settings:
        name = "biz_user"



    def get_avatar(self):
       if  self.avatar != "":
           return self.avatar
       else:
           return "http://xx.xx"


    class Config:
        json_schema_extra = {
            "example": {
                "username": 1,
                "password": "edu",
            }
        }