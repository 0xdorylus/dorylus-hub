import logging


from datetime import datetime
from typing import Optional, List

import pymongo

from beanie import Document, PydanticObjectId, DecimalAnnotation
from agent.utils.common import get_unique_id
from pydantic import BaseModel, Field

class UserStat(Document):
    id:str=Field(default_factory=get_unique_id)
    uid: str
    pid: str = ""
    split_pid:str = ""
    buy_amount:  DecimalAnnotation = Field(decimal_places=8, default=0 )
    total_buy_amount:  DecimalAnnotation = Field(decimal_places=8, default=0 )
    direct_active_child:int=0
    direct_child:int=0
    total_active_team_num:int=0
    total_team_num:int=0
    active: int = 0
    create_at: datetime = datetime.now()
    update_at: datetime = datetime.now()


    @classmethod
    async def get_active_child_list(cls,pid):
        items  = await cls.find({"pid":pid}).to_list()
        return items

    @classmethod
    async def get_active_parent(cls,pid):
        user = await cls.find_one({"uid":pid})
        if user and user.active:
            return user.pid
        else:
            pid = user.pid
            i = 1
            while i < 10000:
                print("i=>",i)
                user = await cls.find_one({"uid": pid})
                if user is None:
                    return None
                if user.active:
                    return user.pid
                else:
                    pid = user.pid
                i+=1

    @classmethod
    async def set_split_parent(cls,pid,uid):
        await cls.find_one({"uid":uid}).update({"$set":{"split_pid":pid}})

    @classmethod
    async def get_split_parent(cls,uid):
        user = await cls.find_one({"uid":uid})
        if user and user.split_pid:
            return user.split_pid
        pid = user.pid
        if pid:
            puser = await cls.find_one({"uid": pid})
            if puser and puser.active:
                return puser.uid
            elif puser:
                i=1
                max=10000
                pid = puser.pid
                while i < max:
                    puser = await cls.find_one({"uid": pid})
                    if puser is None:
                        return None
                    elif puser.active:
                        return puser.pid
                    else:
                        pid = puser.pid
                    i+=1
            else:
                return None
        else:
            logging.info("没有parent")
            return None




    class Settings:
        name = "user_stat"
        indexes = [
            [
                ("uid", pymongo.ASCENDING),
                ("pid", pymongo.ASCENDING)
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