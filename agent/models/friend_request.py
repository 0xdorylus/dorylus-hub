import json
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field
from beanie import Document
from agent.utils.common import get_unique_id

class DealFriendRequestModel(BaseModel):
    id:str
class AddFriendRequestModel(BaseModel):
    target:str
    memo: str=""
class FriendRequestItemModel(BaseModel):
    id:str
    sender:str
    receiver:str
    memo: str
    status:str
    create_at:datetime
class FriendRequestListModel(BaseModel):
    recieve_list:List[FriendRequestItemModel]=[]
    send_list:List[FriendRequestItemModel]=[]

class FriendRequest(Document):
    id:str=Field(default_factory=get_unique_id)
    sender:str
    receiver:str
    memo: str
    status: str="pending"
    create_at: datetime = datetime.now()
    update_at: datetime = datetime.now()

    @classmethod
    async def accept(cls,id):
        await cls.find_one(cls.id==id).update({"$set":{"status":"accept","update_at":datetime.now()}})

    @classmethod
    async def deny(cls, id):
        await cls.find_one(cls.id == id).update({"$set": {"status": "deny", "update_at": datetime.now()}})


    class Settings:
        name = "friend_request"

    class Config:
        json_schema_extra = {
            "example": {


            }
        }


class JoinGroupRequestItem(BaseModel):
    id:str
    uid:str
    channel_id:str
    memo: str
class JoinGroupRequest(Document):
    id:str=Field(default_factory=get_unique_id)
    uid:str
    channel_id:str
    admin_uids:List[str]
    memo: str
    status: str="pending"
    create_at: datetime = datetime.now()
    update_at: datetime = datetime.now()

    @classmethod
    async def accept(cls,uid,id):
        await cls.find_one(cls.id==id).update({"$set":{"status":"accept","update_at":datetime.now()}})

    @classmethod
    async def deny(cls, uid,id):
        await cls.find_one(cls.id == id).update({"$set": {"status": "deny", "update_at": datetime.now()}})


    class Settings:
        name = "join_group_request"

    class Config:
        json_schema_extra = {
            "example": {


            }
        }
