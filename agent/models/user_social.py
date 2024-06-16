import logging

from datetime import datetime
from typing import List

import pymongo

from agent.models.base import BaseDocument
from agent.utils.common import get_unique_id, get_current_time
from pydantic import BaseModel, Field


class UserSocialItem(BaseModel):
    id: str
    icon: str
    link: str


class UserSocialItemList(BaseModel):
    items: List[UserSocialItem] = []


class UserSocial(BaseDocument):
    id: str = Field(default_factory=get_unique_id)
    uid: str
    icon: str
    link: str
    create_at: int = Field(default_factory=get_current_time)
    update_at: int = Field(default_factory=get_current_time)

    class Settings:
        name = "user_social"
        indexes = [
            [
                ("uid", pymongo.ASCENDING),
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

    @classmethod
    async def get_social_list(cls, uid):
        outs: List[UserSocialItem] = []
        items = await cls.find(cls.id == uid).to_list()
        for item in items:
            outs.append(UserSocialItem(**item.model_dump()))
        return outs


class UserDMSetting(BaseDocument):
    id: str = Field(default_factory=get_unique_id)
    uid: str
    limit: int = 1
    create_at: int = Field(default_factory=get_current_time)

    class Settings:
        name = "user_dm_setting"
        indexes = [
            [
                ("uid", pymongo.ASCENDING),
            ],
        ]


class UserFollowNotice(BaseDocument):
    id: str = Field(default_factory=get_unique_id)
    uid: str
    src_uid: str
    src_username: str = ""
    src_avatar: str = ""
    status: str = "pending"
    create_at: int = Field(default_factory=get_current_time)
    update_at: int = Field(default_factory=get_current_time)


class UserFollow(BaseDocument):
    id: str = Field(default_factory=get_unique_id)
    uid: str
    target: str
    status: str = "unread"  # 被关注者还未阅读
    create_at: int = Field(default_factory=get_current_time)

    class Settings:
        name = "user_follow"
        indexes = [
            [
                ("uid", pymongo.ASCENDING),
                ("status", pymongo.ASCENDING),
            ],
        ]

    @classmethod
    async def get_my_following(cls, uid: int):
        await cls.find(cls.uid == uid).to_list()

    @classmethod
    async def get_my_follower(cls, uid: int):
        await cls.find(cls.target == uid).to_list()


class UserTweet(BaseDocument):
    id: str = Field(default_factory=get_unique_id)
    uid: str
    content: str = Field(default="", max_length=2048)
    up_times: int = 0
    down_times: int = 0
    forward_times: int = 0
    reply_times: int = 0
    images: List[str] = []
    tags: List[str] = []
    create_at: int = Field(default_factory=get_current_time)

    class Settings:
        name = "user_tweet"
        indexes = [
            [
                ("uid", pymongo.ASCENDING),
            ],
        ]
