from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, Field
from beanie import Document
from agent.models.base import BaseDocument
from agent.utils.common import get_unique_id, get_mtime, get_current_time
from pydantic import BaseModel, Field
from typing import List


class SendMessageModel(BaseModel):
    id: str
    kind: str
    content: Any
    receiver: str = ""
    sender: str = ""
    channel_id: str
    sig: str = ""
    pubkey: str = ""


class ChatDialogMessageModel(BaseModel):
    id: str
    sender: str
    receiver: str = ""
    content: Any
    channel_id: str
    ref_id: str = ""
    kind: str = "text"
    is_user: bool = True

    create_at: int


class ChatGroupMessageModel(BaseModel):
    id: str
    sender: str
    content: Any
    channel_id: str
    kind: Optional[str] = ""
    create_at: int

class ChatMessagePosition(BaseDocument):
    """
        写扩散的方式做点对点聊天
    """
    id: str = Field(default_factory=get_unique_id)
    uid: str
    channel_id: str
    ack_messagge_id:str=""
    last_message_id: str=""
    update_at:int=get_current_time()

    class Settings:
        name = "chat_message_position"

    @classmethod
    async def update_last_message_id(cls, channel_id, uid, last_message_id):

        r = await cls.find_one({"channel_id": channel_id, "uid": uid}).update(
            {"$set": {"last_message_id": last_message_id}})
        if r.modified_count > 0:
            pass
        else:
            doc = {
                "channel_id": channel_id, "uid": uid, "last_message_id": last_message_id
            }
            await ChatMessagePosition(**doc).create()
    @classmethod
    async def ack_message_id(cls, channel_id, uid, last_message_id):

        r = await cls.find_one({"channel_id": channel_id, "uid": uid}).update(
            {"$set": {"ack_message_id": last_message_id}})
        if r.modified_count > 0:
            pass
        else:
            doc = {
                "channel_id": channel_id, "uid": uid, "ack_message_id": last_message_id
            }
            await ChatMessagePosition(**doc).create()

class ChatGroupUserMessagePosition(BaseDocument):
    """
        写扩散的方式做点对点聊天
    """
    id: str = Field(default_factory=get_unique_id)
    uid: str
    channel_id: str
    last_message_id: str
    update_at:int=get_current_time()

    class Settings:
        name = "chat_group_user_message_position"

    @classmethod
    async def get_last_message_id(cls,channel_id, uid):
        object =  await cls.find_one({"channel_id": channel_id, "uid": uid})
        if object is not None:
            return object.last_message_id
    @classmethod
    async def update_last_message_id(cls, channel_id, uid, last_message_id):

        r = await cls.find_one({"channel_id": channel_id, "uid": uid}).update(
            {"$set": {"last_message_id": last_message_id}})
        if r.modified_count > 0:
            pass
        else:
            doc = {
                "channel_id": channel_id, "uid": uid, "last_message_id": last_message_id
            }
            await ChatGroupUserMessagePosition(**doc).create()


class ChatDialogMessage(BaseDocument):
    """
        写扩散的方式做点对点聊天
    """
    id: str = Field(default_factory=get_unique_id)
    uid: str
    sender: str
    receiver: Optional[str] = ""
    content: Any
    channel_id: str
    ref_id: Optional[str] = ""
    kind: Optional[str] = ""
    answer: str = ""
    pubkey: Optional[str] = ""
    sig: Optional[str] = None
    sent: bool = False
    complete: bool = False
    # ack:Optional[bool]=False
    create_at: int = get_current_time()

    class Settings:
        name = "chat_dialog_message"

    @classmethod
    async def set_answer(cls, id, answer: str):
        await cls.find_one(cls.id == id).update({"$set": {"answer": answer}})

    @classmethod
    async def ack(cls, id):
        await cls.find_one(cls.id == id).update({"$set": {"ack": True}})

    @classmethod
    async  def get_latest_message(cls,uid,channel_id):
        return  await cls.find(cls.channel_id == channel_id,cls.uid==uid).sort(-cls.id).limit(1).first_or_none()

    @classmethod
    async def get_ai_history_pair(cls, channel_id: str, uid: str):
        # print("get_ai_history_pair")
        # print(channel_id,uid)
        objects = await cls.find(cls.channel_id == channel_id).sort(-cls.id).limit(6).to_list()
        history = []
        for data in objects:
            if data.answer:  #
                message_item = []
                message_item.append(data.content)
                message_item.append(data.answer)
                history.append(message_item)
        return history



class ChatGroupMessage(BaseDocument):
    """
        写扩散的方式做点对点聊天
    """
    id: str = Field(default_factory=get_unique_id)
    sender: str
    content: Any
    channel_id: str
    kind: Optional[str] = ""
    receiver_list: Optional[List] = []
    pubkey: Optional[str] = ""
    sig: Optional[str] = None
    create_at: int = get_current_time()
    update_at: int = get_current_time()

    class Settings:
        name = "chat_group_message"

    @classmethod
    async def ack(cls, id):
        """
        确认收到消息
        :param id:
        :return:
        """
    @classmethod
    async def get_latest_message(cls,channel_id):
        return await cls.find(cls.channel_id == channel_id).sort(-cls.id).first_or_none()


class ChatMessage(Document):
    """
        写扩散的方式做点对点聊天
    """
    id: str = Field(default_factory=get_unique_id)
    uid: str
    sender: str
    receiver: Optional[str] = ""
    content: Any
    type: Optional[str] = "dialog"  # group
    channel_id: str
    ref_id: Optional[str] = ""
    kind: Optional[str] = ""
    receiver_list: Optional[List] = []
    pubkey: Optional[str] = ""
    sig: Optional[str] = None
    create_at: datetime = datetime.now()
    update_at: datetime = datetime.now()

    class Settings:
        name = "chat_message"

    @classmethod
    async def get_ai_history_pair(cls, channel_id: str, uid: str):
        #
        # pari[0]是用户消息
        # pair[1]是回复的消息
        objects = await cls.find(cls.channel_id == channel_id).sort(-cls.id).limit(6).to_list()
        history = []
        message_item = []
        question_id = ""
        for object in objects:
            if object.receiver == uid:  # ai messageg
                if len(message_item) == 1 and object.ref_id == question_id:
                    message_item.append(object.content)
                    history.append(message_item)
                    message_item = []
                elif len(message_item) == 1 and object.ref_id != question_id:  # 可能发出问题了，但是AI系统没有回复，就跳过那条记录
                    message_item = []
            else:
                if len(message_item) == 0:
                    message_item.append(object.content)
                    question_id = object.id
        return history

    async def send(cls, id: str, sender: str, receiver: str, content: str, kind: str):
        doc = {
            "id": id,
            "sender": sender,
            "receiver": receiver,
            "content": content,
            "kind": kind,
            "type": "p2p",

        }
