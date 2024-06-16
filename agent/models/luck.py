import logging
import random

from bson import ObjectId
from pydantic import BaseModel, Field
from datetime import datetime
from ipaddress import IPv4Address
from typing import Optional, List, Set

import pymongo
from beanie import Document, Indexed, before_event, after_event

from agent.utils.common import get_unique_id, error_return, encode_input
from agent.utils.common import op_log
from agent.utils.common import success_return
from fastapi import Depends, HTTPException, status
from agent.models.request_response_model import UserInfoModel, UserDetailModel

class LotteryRequestModel(BaseModel):
    id:str=""
    title:str
    num:int
    code:str

class LotteryUserPageRequestModel(BaseModel):
    page: int = 1
    pagesize: int = 100
    id:str

class LotteryUserItem(BaseModel):
    hit:int=0
    uid:str
    user:UserInfoModel={}

class LotteryUserrListModel(BaseModel):
    page:int=0
    total_page:int=0
    list:List[LotteryUserItem]=[]
class LotteryDetailModel(BaseModel):
    id:str
    title:str
    num:int
    code:str
    status:str
    is_admin:bool=False
    create_at: datetime


class LotteryItemModel(BaseModel):
    id:str
    title:str
    num:int
    code:str
    status:str
    create_at: datetime
class LotteryListModel(BaseModel):
    page:int=0
    total_page:int=0
    list:List[LotteryItemModel]=[]
class LotteryJoinModel(BaseModel):
    id:str=""
    code:str
class Lottery(Document):
    id: str = Field(default_factory=get_unique_id,min_length=1)
    uid: str=""
    title: str =  Field("",min_length=1)
    content: str = ""
    code:str = ""
    num:int=1
    status:str="pending"
    create_at: datetime = datetime.now()
    update_at: datetime = datetime.now()
    class Settings:
        name = "lottery"





    @classmethod
    async def start_lucky_time(cls,id,uid):
        lottery = await Lottery.find_one({"_id":id,"uid":uid,"status":"pending"})
        if lottery:
            await Lottery.find_one({"_id": id, "uid": uid, "status": "pending"}).update({"$set":{"status":"started"}})
            items = await LotteryUser.find({"luck_id":id}).to_list();
            random.shuffle(items)
            max_len = len(items)
            num  = lottery.num
            if max_len > num:
                select_items = random.sample(items, num)
                max_len = num
            else:
                select_items = random.sample(items, max_len)
            for i in range(0, max_len):
                user_id = select_items[i].uid
                await LotteryUser.find({"uid": user_id}).update({"$set": {"hit": 1}})
            await Lottery.find_one({"_id": id, "uid": uid}).update({"$set":{"status":"done"}})

            return True
        else:
            return False


class LotteryUser(Document):
    id: str = Field(default_factory=get_unique_id)
    uid: str=""
    luck_id:str
    hit :int=0
    create_at: datetime = datetime.now()
    update_at: datetime = datetime.now()
    class Settings:
        name = "lottery_user"
