from datetime import datetime
from typing import List

import pymongo
from beanie import Document
from bson import ObjectId

from agent.models.base import BaseDocument
from agent.utils.common import get_unique_id, get_current_time
from pydantic import BaseModel, Field, EmailStr

import random


class TaskBox(BaseDocument):
    id: str = Field(default_factory=get_unique_id)
    creator: str
    tag: str = Field(default="channel")  # 是channel、dao还是group、注册
    task_type:str=Field(default="onboard") # 类型 ，选择题、填空题、问答题
    target: str=""  # channel_id,dao_id,
    name: str  # channel_id,dao_id
    desc: str=""  # channel_id,dao_id
    achieve_items: List[str] = []  # 完成的任务后的成就列表
    create_at: int = Field(default_factory=get_current_time)
    update_at: int = Field(default_factory=get_current_time)

    class Settings:
        name = "task_box"

    @classmethod
    async def get_onboarding_task(cls, channel_id:str):
        return await cls.find_one({"target":channel_id,"task_type":"onboard"})



class TaskItem(BaseDocument):
    id: str = Field(default_factory=get_unique_id)
    task_box_id: str  # 任务盒子id
    task_item_type: str = Field(default="single_choice")  # 类型 ，选择题、填空题、问答题
    content: str = Field(default="")  # 内容,json格式根据内容来定
    create_at: int = Field(default_factory=get_current_time)
    update_at: int = Field(default_factory=get_current_time)

    class Settings:
        name = "task_item"


class UserTaskBox(BaseDocument):
    """
        用户参与的task
    """
    id: str = Field(default_factory=get_unique_id)
    uid: str
    task_box_id: str  # 任务盒子id
    task_item_ids: List[str] = []  # 任务盒子id
    is_finished: bool = False
    total_num: int = 0 #cache
    finished_num: int = 0 #cache
    is_skipped: bool = False #用户跳过
    create_at: int = Field(default_factory=get_current_time)
    update_at: int = Field(default_factory=get_current_time)
    class Settings:
        name = "user_task_box"

class UserTaskItem(BaseDocument):
    id: str = Field(default_factory=get_unique_id)
    uid: str
    task_item_id: str = Field(default="single_choice")  # 类型 ，选择题、填空题、问答题
    content: str = Field(default="")  # 内容,json格式根据内容来定
    is_finished: bool = False
    create_at: int = Field(default_factory=get_current_time)
    update_at: int = Field(default_factory=get_current_time)