import logging

from bson import ObjectId
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from ipaddress import IPv4Address

import pymongo
from beanie import Document, Indexed, before_event,after_event
import secrets
from beanie import Document, PydanticObjectId
from beanie import Insert

from pydantic import BaseModel

from agent.models.base import BaseDocument


class Memory(Document):
    uid: str
    task_id: str
    name: str
    url:str
    assistant_id:str
    max_tokens:int
    create_at: datetime = datetime.now()
    update_at: datetime = datetime.now()

    @before_event(Insert)
    async def generate_invite_code(self):
        logging.info("before insert")

    @after_event(Insert)
    async def init_stat(self):
        logging.info("after insert")

class Task(Document):
    uid: str
    task_id: str
    name: str
    url:str
    assistant_id:str
    max_tokens:int
    create_at: datetime = datetime.now()
    update_at: datetime = datetime.now()

    @before_event(Insert)
    async def generate_invite_code(self):
        logging.info("before insert")

    @after_event(Insert)
    async def init_stat(self):
        logging.info("after insert")


    @classmethod
    async def by_task_id(cls, task_id: str) -> "Task":
        """Get a user by address"""
        return await cls.find_one(cls.task_id == task_id)



    @classmethod
    async def by_uid(cls, uid: str) -> "Task":
        """Get a user by uid"""
        return await cls.find_one(cls.uid == uid)

    class Settings:
        name = "task"

        # indexes = [
        #     [
        #         ("address", pymongo.TEXT),
        #         ("username", pymongo.TEXT),
        #         ("invite_code", pymongo.TEXT),
        #         ("email", pymongo.TEXT),
        #         ("uid",pymongo.ASCENDING)
        #     ],
        # ]

    class Config:
        json_schema_extra = {
            "example": {
                "username": "bots001",
                "address": "0xE91C299427D5DB24Dcc064db3Dc42d1bF1bf187E",
            }
        }

class TaskForm(BaseModel):
    op:str
    uid: str
    task_id: str
    name: Optional[str] = ""
    file_path: Optional[str] = ""
    url: Optional[str] = ""
    assistant_id:str
    max_tokens:int
    callback_url:Optional[str]
    doc_id:Optional[str]
    file_digest:Optional[str]

    class Config:
        populate_by_name = True
        json_schema_extra = {
            'example': {
                'uid': "111",
                'task_id': '1111',
                'name': 'John',
                'file_path': '/User/file/path',
                'url':'http://127.0.0.1/task/xx',
                'assistant_id':'111',
                'max_tokens':100,

            }
        }

class AskForm(BaseModel):
    uid: str
    prompt: str
    assistant_id: str
    doc_ids: list
    temperature: Optional[float] = 0.7
    user_prompt:Optional[str]=""
    system_prompt:Optional[str]=""




class Prompt(BaseDocument):
    uid: str
    task_id: str
    name: str
    url:str
    assistant_id:str
    max_tokens:int
    create_at: datetime = datetime.now()
    update_at: datetime = datetime.now()

    @before_event(Insert)
    async def generate_invite_code(self):
        logging.info("before insert")

    @after_event(Insert)
    async def init_stat(self):
        logging.info("after insert")


    @classmethod
    async def by_task_id(cls, task_id: str) -> "Task":
        """Get a user by address"""
        return await cls.find_one(cls.task_id == task_id)



    @classmethod
    async def by_uid(cls, uid: str) -> "Task":
        """Get a user by uid"""
        return await cls.find_one(cls.uid == uid)

    class Settings:
        name = "task"

        # indexes = [
        #     [
        #         ("address", pymongo.TEXT),
        #         ("username", pymongo.TEXT),
        #         ("invite_code", pymongo.TEXT),
        #         ("email", pymongo.TEXT),
        #         ("uid",pymongo.ASCENDING)
        #     ],
        # ]

    class Config:
        json_schema_extra = {
            "example": {
                "username": "bots001",
                "address": "0xE91C299427D5DB24Dcc064db3Dc42d1bF1bf187E",
            }
        }