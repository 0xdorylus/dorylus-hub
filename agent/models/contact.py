import logging

from beanie import Document
from fastapi import HTTPException
from pydantic import Field

from agent.config import CONFIG
from agent.models.base import BaseDocument, GenericResponseModel
from agent.models.channel import Channel
from agent.utils.common import get_unique_id, get_current_time

from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Set


class ContactItemModel(BaseModel):
    id: str = ""
    username: str = Field("", description="用户名")
    channel_id: str = ""
    receiver: str = Field("", description="对方的UID，AI机器人和点对点试用")
    memo: str = Field("", description="备注名")
    avatar: str = ""


class ContactListItemModel(BaseModel):
    id: str
    username: str
    channel_id: str
    receiver: str
    memo: str = ""
    avatar: str
    user:dict={}
    type: str = Field("", description="类型,group:群,p2p：人和人,p2m ：人和机器")


class ContactListResponseModel(BaseModel):
    total: int = 0
    total_page: int = 0
    list: List[ContactListItemModel] = []


class Contact(BaseDocument):
    id: str = Field(default_factory=get_unique_id)
    uid: str
    avatar: str = ""
    username: str = ""
    receiver: str = ""
    channel_id: str
    memo: str = ""
    type: str = ""
    create_at: int = get_current_time()
    update_at:  int = get_current_time()

    class Settings:
        name = "contact"

    @classmethod
    async def upsert(cls, uid: str, form: ContactItemModel):
        channel = await Channel.get(form.channel_id)
        if not channel:
            return GenericResponseModel(code=404, message="not_found_channel")
        if form.id == "":
            """
            insert
            """
            doc = form.model_dump()
            doc['uid'] = uid
            del doc['id']
            await Contact(**doc).create()
        else:
            data = {k: v for k, v in form.items() if v is not None and v != "" and v != []}
            data['update_at'] = datetime.now()
            update = {"$set": data}
            await Contact.find_one(Contact.id == form.id).update(update)

        return GenericResponseModel()

    @classmethod
    async def add_pair_contact(cls, uid: str, target:str,target_user_name:str,target_user_avatar:str,channel_id:str):

        contact = await cls.find_one({
            "uid": uid,
            "receiver": target,
            "channel_id": channel_id,
            "type": "pair"
        })
        if contact is None:
            doc = {
                "uid": uid,
                "receiver": target,
                "username": target_user_name,
                "avatar": target_user_avatar,
                "channel_id": channel_id,
                "type": "pair",
            }
            await Contact(**doc).create()
            logging.info("add_pair_contact")
        else:
            logging.info("pair_contact_exist")
