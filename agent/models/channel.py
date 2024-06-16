import logging

import pymongo


from agent.config import CONFIG
from agent.models.base import BaseDocument

from agent.models.user_social import UserDMSetting
from agent.utils.common import get_unique_id, get_current_time

from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Set

class ChanndelItemModel(BaseModel):
    id:str
    uid:str
    user_ids: List[str]=[]
    type:str
    category:Optional[str]=""
    name:str
    intro:str
    logo:str
    banner:str
    admin_ids: List[str]=[]
    tag_ids: List[str]=[]
    link:str=""
    join_channel_link:str=""
    user_in_channel:bool=False
    is_admin:bool=False
    target:str=""
    memo:str=""

class Channel(BaseDocument):
    """
        用于存储用户创建的频道
        点对点和群聊都可以
    """
    id:str=Field(default_factory=get_unique_id)
    uid:str
    target:Optional[str]=""
    user_ids: List[str]=[]  # 用户
    agent_ids: List[str]=[] # 机器人
    admin_ids: List[str]=[] # 管理员
    tag_ids: List[str]=[]   # 标签
    type:Optional[str]="p2p"   # p2p,p2m,group
    category:Optional[str]=""   # 分类
    name:Optional[str]=""   # 名称
    intro:Optional[str]=""  # 简介
    logo:Optional[str]=""   # logo
    banner:Optional[str]="" # banner

    who_can_join:str="anyone"
    link:str=""            # 链接

    create_at: int = Field(default_factory=get_current_time)
    update_at: int = Field(default_factory=get_current_time)

    @classmethod
    async def is_user_in_admin(cls,uid:str,channel_id:str):
        channel = await cls.find_one({"_id":channel_id,"admin_ids":{"$in":[uid]}})
        if channel is not None:
            return True
        else:
            return False
    @classmethod
    async def is_user_in_channel(cls,uid:str,channel_id:str):
        channel = await cls.find_one({"_id":channel_id,"user_ids":{"$in":[uid]}})
        if channel is not None:
            return True
        else:
            return False
    @classmethod
    async def get_pair_channel(cls, uid: str, target: str):
        if uid > target:
            uid, target = target, uid
        channel = await cls.find_one({'uid': uid, 'target': target,'type':'pair'})
        if channel is not None:
            return channel

    @classmethod
    async def try_create_pair_channel(cls, uid:str, target:str):
        """
            用索引限制uid target不重复
        """
        if uid > target:
            uid, target = target, uid
        channel = await cls.find_one({'uid': uid, 'target': target})
        if channel is not None:
            return channel
        data = {
            "uid": uid,
            "target": target,
            "user_ids": [uid, target],
            'type':'pair'
        }
        logging.info("create_pair_channel",data)
        channel =await Channel(**data).create()
        return channel




    @classmethod
    async def try_drop_pair_channel(cls, uid:str, target:str):
        if uid > target:
            uid, target = target, uid
        await cls.find_one({'uid': uid, 'target': target, "type":"pair"}).delete()


    @classmethod
    async def can_chat(cls,uid:str,target:str):
        if uid > target:
            uid, target = target, uid

        channel = await cls.find_one({'uid': uid, 'target': target})
        if channel is not None:
            return True
        else:
            setting = await UserDMSetting.find_one({"uid":target})
            if setting and setting.limit ==0:
                return True
            return False

    def get_avatar(self):
        if self.logo:
            return self.logo
        else:
            return CONFIG.default_channel_avatar


    @classmethod
    async def get_channel(cls,uid:str,target:str):
        if uid > target:
            uid, target = target, uid
        channel = await cls.find_one({
                "uid": uid,
                "target": target,
            })
        return channel
    @classmethod
    async def get_receiver_list(cls,channel_id:str,uid:str):

        channel = await cls.find_one({"_id":channel_id,"user_ids":{"$in":[uid]}})
        if channel:
            return channel.user_ids #[t for t in channel.user_ids if t != uid]
        else:
            return []
    @classmethod
    async def get_pairl_receiver(cls,channel_id:str,uid:str):
        channel = await cls.find_one(cls.id == channel_id)
        if channel:
            return [t for t in channel.user_ids if t != uid][0]
        else:
            return ""
    @classmethod
    async def drop_ai_channel(cls,uid:str,target:str):

        r = await cls.find_one(
            {
                "uid": uid,
                "target": target,
            }).delete()
        logging.info("drop_ai_channel,",r)

    @classmethod
    async def get_ai_channel(cls,uid:str,target:str):

        channel = await cls.find_one(
            {
                "uid": uid,
                "target": target,
                "type": "p2m"
            })
        return channel

    @classmethod
    async def create_ai_channel(cls,uid:str,target:str):
        """
            用索引限制uid target不重复


        """
        channel = await cls.find_one(
            {
                "uid": uid,
                "target": target,
                "type": "p2m"
            })

        if channel:
            return channel

        data = {
            "uid":uid,
            "target":target,
            "user_ids":[uid,target],
            "type":"p2m"
        }
        return await Channel(**data).create()

    @classmethod
    async def create_friend_channel(cls,uid:str,target:str):
        channel = await cls.find_one(
            {
                "uid": uid,
                "target": target,
                "type": "p2p"
            })

        if channel:
            return channel

        data = {
            "uid":uid,
            "target": target,
            "user_ids":[uid,target],
            "type":"p2p"
        }
        return await Channel(**data).create()

    async def user_join_channle(self,uid):
        if uid not in self.user_ids:
            self.user_ids.append(uid)
            await self.save()
            print("user_join_channle",self.user_ids)
        return True




    class Settings:
        name = "channel"

        indexes = [
            "idx_who_target_type",
            [
                ("uid", pymongo.ASCENDING),
                ("target", pymongo.DESCENDING),
                ("type", pymongo.DESCENDING),
            ],
        ]

    class Config:
        json_schema_extra = {
            "example": {
                "title": "tag",
                "value": "name",
            }
        }



class ChannelFile(BaseDocument):
    id:str=Field(default_factory=get_unique_id)
    uid:str
    channel_id:str
    filename:str
    url:str
    size:int
    content_type:str=""
    create_at:int= Field(default_factory=get_current_time)


    class Settings:
        name = "channel_file"



    class Config:
        json_schema_extra = {
            "example": {
            }
        }

