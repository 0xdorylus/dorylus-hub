import logging

from bson import ObjectId, Decimal128
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from ipaddress import IPv4Address

import pymongo
from beanie import Document, Indexed, before_event, after_event
import secrets
from beanie import Document, PydanticObjectId
from beanie import Insert

from agent.models.agent import Agent
from agent.models.assistant import Assistant, Girl
from agent.models.base import BaseDocument
from agent.models.channel import Channel
from agent.models.chat_message import ChatGroupMessage, ChatDialogMessage
from agent.models.contact import Contact, ContactItemModel
from agent.models.user import User
from agent.utils.common import get_unique_id, get_current_time

from agent.utils.common import success_return
from agent.utils.common import op_log


class ConversationListItem(BaseModel):
    uid: str
    target: str
    channel_id: str
    type: str
    message: str = ""
    new_message_num: int
    avatar: str
    status: int
    nickname: str = ""
    name: Optional[str] = ""

    # for girl
    closeness: int = 0
    is_lock: bool = False
    background: str = ""
    update_at: int


class ConversationList(BaseModel):
    items: List[ConversationListItem] = []


class Conversation(BaseDocument):
    id: str = Field(default_factory=get_unique_id)
    uid: str
    target: str
    channel_id: str
    type: str
    name: Optional[str] = ""
    message: str = ""
    avatar: str = ""
    new_message_num: int = 0
    status: int = 1
    update_at: int = Field(default_factory=get_current_time)

    @classmethod
    async def set_ai_last_messae(cls, uid, target, answer):
        print("set_ai_last_messae", uid, target, answer)
        update = {
            "message": answer,
            "update_at": get_current_time()
        }
        r = await cls.find_one({"uid": uid, "target": target, 'type': 'p2m'}).update({"$set": update})
        print(r)


    @classmethod
    async def set_p2p_last_message(cls, channel_id, uid, answer):
        update = {
            "message": answer,
            "update_at":  get_current_time()
        }
        await cls.find_one({"channel_id": channel_id, 'uid': uid, 'type': 'p2p'}).update({"$set": update});

    @classmethod
    async def set_group_last_messae(cls, channel_id, content):
        update = {
            "message": content,
            "update_at": get_current_time()
        }
        await cls.find({"channel_id": channel_id, 'type': 'group'}).update({"$set": update});

    @classmethod
    async def add_group_conversation(cls, uid, channel_id, name):
        channel = await Channel.get(channel_id)
        doc = {
            'uid': uid,
            'channel_id': channel_id,
            "target": "",
            "name": name,
            'avatar': channel.get_avatar(),
            'type': 'group',
        }
        o = await Conversation.find_one({'uid': uid,
                                         'channel_id': channel_id, 'type': 'group'})
        if o is None:
            await Conversation(**doc).create()

    @classmethod
    async def drop_group_conversation(cls, uid, channel_id):
        await Conversation.find_one({'uid': uid, 'channel_id': channel_id, 'type': 'group'}).delete()

    @classmethod
    async def add_friend_conversation(cls, uid, target, channel_id):
        user = await User.get(target)

        contact = await cls.find_one({
            'uid': uid,
            'target': target,
            'channel_id': channel_id,
        })
        if contact is None:
            if user.user_type == "agent":
                c_type = "p2m"
            else:
                c_type = "p2p"
            doc = {
                'uid': uid,
                'target': target,
                'channel_id': channel_id,
                'avatar': user.get_avatar(),
                'type': c_type,
            }
            await Conversation(**doc).create()



    # @classmethod
    # async def add_agent_conversation(cls, uid: str, target: str, channel_id: str):
    #     # 最进会话
    #     agent = await Agent.get(target)
    #     doc = {
    #         'uid': uid,
    #         'target': target,
    #         'channel_id': channel_id,
    #         'avatar': agent.get_avatar(),
    #         'type': 'p2m',
    #     }
    #     await Conversation(**doc).create()
    #
    #     # 联系人
    #     form = ContactItemModel(
    #         uid=uid,
    #         username=agent.name,
    #         channel_id=channel_id,
    #         receiver=target,
    #         memo="",
    #         avatar=agent.get_avatar(),
    #         type="p2m"
    #     )
    #     await Contact.upsert(uid, form)

    @classmethod
    async def drop_assistant_conversation(cls, uid, target):
        where = {
            'uid': uid,
            'target': target,
            'type': 'p2m',
        }
        await cls.find_one(
            where).delete()

    @classmethod
    async def drop_friend_conversation(cls, uid, target):
        where = {
            'uid': uid,
            'target': target,
            'type': 'p2p',
        }
        await cls.find_one(
            where).delete()

    @classmethod
    async def get_chats(cls, uid):
        chats: List[ConversationListItem] = []
        items = await cls.find({"uid": uid}).to_list()
        for item in items:
            doc = ConversationListItem(**item.model_dump())

            if item.type == "group":
                message = await ChatGroupMessage.get_latest_message(item.channel_id)
                if message is not None:
                    if  'filename' in message.content:
                        doc.message = message.content['filename']
                    elif  isinstance(message.content, str):
                        doc.message = message.content
                    else:
                        doc.message = "..."
            # if item.type == "p2p" or item.type == "pair" or item.type == "p2m":
            else:
                target = item.target
                contact = await Contact.find_one({"receiver": item.target, "uid": uid})
                if contact is not None and contact.memo != "":
                    doc.name = contact.memo
                else:
                    user = await User.get(target)
                    doc.name = user.get_username()

                if item.type == "p2m":
                    pass
                else:
                    message = await ChatDialogMessage.get_latest_message(uid, item.channel_id)
                    if message is not None:
                        if 'content' in message and isinstance(message['content'], dict) and 'filename' in message[
                            'content']:
                            doc.message = message['content']['filename']
                        elif 'content' in message and isinstance(message['content'], str):
                            doc.message = message['content']
                        else:
                            doc.message = "..."
                    else:
                        print(doc)
                        doc.message = "..."

            chats.append(doc)
        return chats

    class Settings:
        name = "conversation"
