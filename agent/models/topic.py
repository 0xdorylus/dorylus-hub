from datetime import datetime
from typing import List

import pymongo
from beanie import Document
from bson import ObjectId

from agent.models.base import BaseDocument
from agent.utils.common import get_unique_id, get_current_time
from pydantic import BaseModel, Field, EmailStr

import random

class Topic(BaseDocument):
    id: str = Field(default_factory=get_unique_id)
    tag: str
    question: str
    create_at: int = Field(default_factory=get_current_time)
    class Settings:
        name = "topic"


    @classmethod
    async def get_random_question(cls,tag,num:int=3):
        items = await cls.find({"tag":tag}).to_list()
        random.shuffle(items)
        max_len = len(items)
        if max_len > num:
            select_items = random.sample(items, num)
            max_len = num
        else:
            select_items = random.sample(items, max_len)
        return select_items

    @classmethod
    async def get_tags(cls):
        items = await cls.distinct("tag",{})
        return items

    @classmethod
    async def get_topics(cls):
        items = await cls.distinct("tag",{})
        out = {
        }
        for tag in items:
            out[tag] = []
        for tag in items:
            topics = await cls.find({"tag": tag}).to_list()
            for vo in topics:
                out[tag].append(vo.question)

        return out

