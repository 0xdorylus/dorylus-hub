import logging

from datetime import datetime
from typing import Optional, List

import pymongo

from beanie import Document, PydanticObjectId

from agent.models.base import BaseDocument
from agent.utils.common import get_unique_id
from pydantic import BaseModel, Field


class UserAchievementCounterModel(BaseModel):
    tag: str
    num: int


class UserAchievementItem(BaseModel):
    id: str
    uid: str
    tag: str = Field("", description="用户成就分类")
    logo: str
    name:str=""
    logo2:str=""
    nft_id: str
    contract: str
    chain: str
    intro: str
    limit_num: int
    user_num:int


class UserAchievementTagModel(BaseModel):
    tag: str
    list: List[UserAchievementItem]


class UserAchievementStatModel(BaseModel):
    tag_counter_list: List[UserAchievementCounterModel] = []
    tag_items_list: List[UserAchievementTagModel] = []


class AchievementItem(BaseModel):
    id: str = Field("", description="成就ID，为空新增，不为空修改")
    tag: str = Field("", description="成就分类，比如POA")
    logo: str = Field("", description="Logo")
    name:str= Field("", description="name")
    logo2:str= Field("", description="Logo2")
    nft_id: str = Field("", description="NFT的ID")
    contract: str = Field("", description="合约地址")
    chain: str = Field("", description="所属链")
    intro: str = Field("", description="成就说明")
    limit_num: int = Field(0, description="用户成就门槛，比如是交谈10次")


class UserAchievementRequestItem(BaseModel):
    id: str=""
    num:int=0
    achieve_id:str

class Achievement(BaseDocument):
    """
        成就，包括徽章，POAP等等
    """
    id: str = Field(default_factory=get_unique_id)
    tag: str = Field("", description="用户成就分类")
    logo: str = ""
    name:str= Field("", description="name")
    logo2:str= Field("", description="Logo2")
    nft_id: str = ""
    contract: str = ""
    chain: str = ""
    intro: str = ""
    limit_num: int = Field(5, description="用户成就门槛，比如是交谈10次")
    create_at: datetime = datetime.now()
    update_at: datetime = datetime.now()

    class Settings:
        name = "achievement"
        indexes = [
            [
                ("uid", pymongo.ASCENDING),
            ],
        ]

    class Config:
        json_schema_extra = {
            "example": {
                "uid": "1",
            }
        }


class UserAchievement(Achievement):
    id: str = Field(default_factory=get_unique_id)
    uid: str
    achieve_id:str
    num: int = 0

    class Settings:
        name = "user_achievement"
        indexes = [
            [
                ("uid", pymongo.ASCENDING),
            ],
        ]

    class Config:
        json_schema_extra = {
            "example": {
                "uid": "1",
            }
        }

    @classmethod
    async def get_achieve(cls,uid,name,num):
        achive = await Achievement.find_one({"name":name})
        if achive:
            user_achive = UserAchievement.find_one(
                {
                    "uid": uid,
                    "achieve_id": achive.id
                }
            )
            if user_achive:
                pass
            else:
                doc={
                    "uid": uid,
                    "achieve_id": achive.id,
                    "num":num
                }
                await cls(**doc).create()
                msg = f"uid get achive %d ,num:%d" % (achive.id,num)
                logging.info(msg)
        else:
            print("error achieve")


    @classmethod
    async def get_stat_list(cls, uid):
        tag_counter_list: List[UserAchievementCounterModel] = []
        tag_items_list: List[UserAchievementCounterModel] = []

        items = await cls.find(cls.uid == uid).to_list()
        tag_count_dict = {}
        tag_items_dict = {}
        for item in items:
            o = UserAchievementItem(**item.model_dump())
            if item.tag in tag_count_dict:
                tag_count_dict[item.tag] += 1
                tag_items_dict[item.tag].append(o)

            else:
                tag_count_dict[item.tag] = 1
                tag_items_dict[item.tag] = []
                tag_items_dict[item.tag].append(o)
        print(tag_counter_list)
        print(tag_items_dict)
        for key in tag_count_dict.keys():
            tag_counter_list.append(UserAchievementCounterModel(tag=key, num=tag_count_dict.get(key)))
        for key in tag_items_dict.keys():
            print("===>",key)
            tag_items_list.append(UserAchievementTagModel(tag=key,list= tag_items_dict.get(key)))

        return UserAchievementStatModel(tag_counter_list=tag_counter_list, tag_items_list=tag_items_list)
