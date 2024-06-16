import logging

from bson import ObjectId
from pydantic import BaseModel, Field
from datetime import datetime
from ipaddress import IPv4Address
from typing import Optional, List, Set

import pymongo
from beanie import Document, Indexed, before_event, after_event
import secrets
from beanie import Document, PydanticObjectId
from beanie import Insert

from .assistant import Assistant
from .base import BaseDocument
from .channel import Channel
from .counter import Counter
from .subscribe import Subscription
from .user_stat import UserStat
from .user_asset import UserAsset
from pydantic import BaseModel

from agent.utils.common import get_unique_id, error_return, encode_input, get_current_time
from agent.utils.common import op_log
from agent.utils.common import success_return
from fastapi import Depends, HTTPException, status
from agent.models.request_response_model import UserInfoModel, UserDetailModel

from agent.config import CONFIG



class UserPromotionLogItemModel(BaseModel):
    uid: str
    op_type: str
    desc: str
    create_at: int


class UserPromotionLogPageModel(BaseModel):
    total: int = 0
    page: int = 1
    total_page: int = 1
    list: List[UserPromotionLogItemModel]


class UserPromotionItemModel(BaseModel):
    username: str = ""
    create_at: int
    avatar: str
    level: int
    id: str


class UserPromotionPageModel(BaseModel):
    total: int = 0
    page: int = 1
    total_page: int = 1
    list: List[UserPromotionItemModel]


# 定义用户模型
class UpdateUserModel(BaseModel):
    username: str = ""
    avatar: str = ""
    nickname: str = ""
    email: str = ""
    intro: str = ""
    language: str = ""
    password: str = ""
    trade_password: str = ""
    type: str = ""
    gender: str = ""
    birthday: str = ""
    interests: List[str] = []
    personality: List[str] = []
    goals: str = ""
    horoscope: str = ""
    pid: str = ""

    class Config:
        populate_by_name = True
        json_schema_extra = {
            'example': {
                'username': 'han',
                'nickname': 'John',
                'intro': '',
                'password': '',
                'trrade_password': '',
                'type': '',
                'language': 'en',
                'gender': '',
                'birthday': '',
                'interests': [],
                'personality': [],
                'goals': '',
                'horoscope': '',
                'pid': '',
            }
        }


class UserSecurity(BaseDocument):
    id: str
    ga_secret: Optional[str] = ""
    create_at: int = Field(default_factory=get_current_time)
    update_at: int = Field(default_factory=get_current_time)



class User(BaseDocument):
    id: str = Field(default_factory=get_unique_id)
    app_uid: Optional[str] = ""
    pid: Optional[str] = ""
    owner: Optional[str] = ""  # 一个用户可能创建多个子账号，owner是主账号

    username: Optional[str] = ""  # 用户，唯一
    nickname: Optional[str] = ""  # 昵称，不唯一
    device_id: Optional[str] = ""  # 设备ID，不唯一
    address: Optional[str] = ""  # 地址，不唯一
    withdraw_address: Optional[str] = ""  # 提现地址，不唯一

    email: Optional[str] = ""
    avatar: Optional[str] = ""
    password: Optional[str] = ""
    trade_password: Optional[str] = ""
    normlized_email: Optional[str] = ""
    lang: Optional[str] = "en"
    # User information
    first_name: Optional[str] = ""
    last_name: Optional[str] = ""
    disabled: bool = False
    status: int = 1
    intro: Optional[str] = ""
    email_confirmed: bool = False
    register_host: Optional[str] = ""
    invite_code: Optional[str] = ""
    verified: bool = False
    assistant_num: int = 0
    level: int = 0
    user_type: str = ""
    agent_ids: Optional[List] = []
    accept_invite_join_group: bool = True

    gender: Optional[str] = ""
    birthday: Optional[str] = ""
    interests: Optional[List[str]] = []
    personality: Optional[List[str]] = []
    goals: Optional[str] = ""
    horoscope: Optional[str] = ""


    last_login_ip: Optional[str] = ""
    last_login_at: int = Field(default_factory=get_current_time)
    create_at: int = Field(default_factory=get_current_time)
    update_at: int = Field(default_factory=get_current_time)

    @classmethod
    async def set_parent(cls, uid, pid):
        await cls.find_one(User.id == uid).update({"$set": {"pid": pid}})
        await UserStat.find_one(User.id == uid).update({"$set": {"pid": pid}})

    @classmethod
    async def get_parents_ids(cls, uid, height=10000):
        parents = []
        i = 0
        while i < height:
            user = await cls.find_one(User.id == uid)
            if user:
                if i != 0:  # not self
                    parents.append(user.id)
                if user.pid != "":  # have parent
                    uid = user.pid
                else:
                    break
            else:
                break
            i = i + 1

        return parents

    @classmethod
    async def get_withdraw_address(cls, uid):
        user = await cls.find_one(User.id == uid)
        if user.withdraw_address != "":
            return user.withdraw_address
        elif user.address != "":
            return user.address
        else:
            return None

    @classmethod
    async def set_vip_level(cls, uid):
        await cls.find_one(User.id == uid).update({"$set": {"level": 1}})

    @classmethod
    async def set_lang(cls, uid: str, lang: str):
        print(uid)
        print(lang)
        await cls.find_one(User.id == uid).update({"$set": {"lang": lang}})

    @classmethod
    async def kill_self(cls, uid):
        await op_log("kill_self", uid)
        await cls.find_one(User.id == uid).delete()

    @classmethod
    async def get_info(cls, uid):
        user = await cls.find_one(User.id == uid)
        if user:
            user.avatar = user.get_avatar()
            user.username = user.get_username()
            return UserInfoModel(**user.model_dump())


        else:
            UserInfoModel(**{
                "id": "",
                "email": "",
                "avatar": "",
                "username": "",
            })

    def get_avatar(self):
        if self.avatar:
            return self.avatar
        else:
            return CONFIG.default_user_avatar
    def update_avatar(self,value=""):
        if value != "":
            self.avatar = value
        elif self.avatar == "":
            self.avatar = CONFIG.default_user_avatar

    def get_username(self):
        if self.nickname:
            return self.nickname
        elif self.username:
            return self.username

        elif self.address:
            return self.address
        elif self.email:
            return self.email
        elif self.device_id:
            return self.device_id
        else:
            return "unknown"

    def get_invite_link(self):
        return CONFIG.invite_domain + "#/login?refcode=" + self.invite_code

    @classmethod
    async def update_profile(cls, uid: str, update_user: UpdateUserModel):
        if update_user.username:
            user = await cls.find_one(cls.username == update_user.username)
            if user and user.id != uid:
                raise HTTPException("username exists")
        data = {k: v for k, v in update_user.model_dump().items() if v is not None and v != "" and v != [] and v != 0}

        print(data)

        for k, v in data.items():
            print(k, v)

        update_query = {"$set": {
            field: value for field, value in data.items()
        }}
        print(update_query)
        await cls.find_one(cls.id == uid).update(update_query)

        await op_log("update_profile", uid)

        data = await cls.find_one(cls.id == uid)
        return UserDetailModel(**data.dict())

    @before_event(Insert)
    async def generate_invite_code(self):
        if not self.invite_code:
            while True:
                invite_code = secrets.token_hex(4)
                user = await User.find_one(User.invite_code == invite_code)
                if not user:
                    self.invite_code = invite_code
                    break

    @after_event(Insert)
    async def init_stat(self):

        self.create_at = get_current_time()
        await UserStat(uid=self.id, pid=self.pid, address=self.address).create()
        logging.info(("user stat created"))

        for token in CONFIG.token_list:
            await UserAsset(uid=self.id, mainchain="BSC", token=token).create()

    @classmethod
    async def by_address(cls, address: str) -> "User":
        """Get a user by address"""
        return await cls.find_one(cls.address == address)

    @classmethod
    async def by_email(cls, email: str) -> "User":
        """Get a user by email"""
        return await cls.find_one(cls.email == email)

    @classmethod
    async def by_uid(cls, uid: int) -> "User":
        """Get a user by uid"""
        return await cls.find_one(cls.id == uid)

    @classmethod
    async def delegate_assistant(cls, uid: str, assistant_id: str):
        await op_log("unsubscribe_assistant uid %s %s ", uid, assistant_id)
        assistant = await Assistant.find_one(Assistant.id == assistant_id, Assistant.uid == uid)
        if assistant:

            ret = await cls.find_one(cls.id == uid, ).update({"$set": {cls.delegate_assistant_id: assistant_id}})
            logging.info(ret)

            return success_return(ret)
        else:
            return error_return("")

    @classmethod
    async def set_property(cls,uid:str,key:str,value:str):
        r =  await cls.find_one(cls.id == uid).update({"$set": {key: value, "update_at": get_current_time()}})
        if r.modified_count > 0:
            return success_return(True)
        else:
            return error_return(1,"not_changed")

    class Settings:
        name = "user"

        indexes = [
            [
                ("address", pymongo.TEXT),
                ("username", pymongo.TEXT),
                ("invite_code", pymongo.TEXT),
                ("email", pymongo.TEXT),
                ("uid", pymongo.ASCENDING)
            ],
        ]

    class Config:
        json_schema_extra = {
            "example": {
                "username": "bots001",
                "address": "0xE91C299427D5DB24Dcc064db3Dc42d1bF1bf187E",
            }
        }


# 定义用户模型
class UpdateContact(BaseModel):
    uid: int
    target_uid: int
    name: str
    address: str = None
    pubkey: str = None
    priority_level: int = 0

    class Config:
        populate_by_name = True
        json_schema_extra = {
            'example': {
                'uid': 1,
                'username': 'han',
                'nickname': 'John',
                'address': '0xE91C299427D5DB24Dcc064db3Dc42d1bF1bf187E'
            }
        }


class LoginWithUsernameModel(BaseModel):
    username: str
    password: str

    class Config:
        populate_by_name = True
        json_schema_extra = {
            'example': {
                'username': 'han',
                'password': 'John',
            }
        }


class LoginWithSignModel(BaseModel):
    address: str = Field("", description="区块链钱包地址", max_length=42)
    msg: str = Field("", description="签名的消息", max_length=512)
    sig: str = Field("", description="签名", max_length=256)
    nonce: str = Field("", description="随机数", max_length=32)
    refcode: Optional[str] = Field("", description="邀请码", max_length=32)
    client_id: Optional[str] = Field("", description="客户端ID", max_length=32)

    class Config:
        populate_by_name = True
        json_schema_extra = {
            'example': {
                'address': '0xc6e8dbbf0170f430fbf8f2abb9097fd47457709d',
                'nonce': 'nonceseq',
                'msg': 'Login in(Seq:212491)',
                'sig': '0x567b526c4df29469aad99ab7e7b2fb648594aa07780230606dd578b62c5f191e103344ee20a9f27259c8e17ea8ffc97261f5bd29614920f780dde4515909e6041b',
                'refcode': '',
                'client_id': ''
            }
        }


class LoginWithUsername(BaseModel):
    username: str
    password: str
    client_id: Optional[str]

    class Config:
        populate_by_name = True
        json_schema_extra = {
            'example': {
                'username': 'han',
                'password': 'botisfuture',
                'client_id': 'client_id'
            }
        }


class SignUpWithEmailModel(BaseModel):
    email: str
    password: str
    invite: Optional[str] = ""
    captcha: Optional[str] = ""

    class Config:
        populate_by_name = True
        json_schema_extra = {
            'example': {

                "email": "hong@irole.networrk",
                "password": "A1681691688=",
                "invite": "",
                "captcha": ""

            }
        }


class LoginWithEmailModel(BaseModel):
    email: str
    password: str
    captcha: Optional[str] = ""

    class Config:
        populate_by_name = True
        json_schema_extra = {
            'example': {

                "email": "hong@irole.networrk",
                "password": "A1681691688=",
                "captcha": ""

            }
        }


class VerifyEmailModel(BaseModel):
    email: str
    code: int

    class Config:
        populate_by_name = True
        json_schema_extra = {
            'example': {

                "email": "service@mail.0xbot.org",
                "code": "111111"

            }
        }
