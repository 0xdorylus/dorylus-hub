import logging

from bson import ObjectId, Decimal128
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Annotated
from ipaddress import IPv4Address
from decimal import Decimal
from agent.connection import get_next_id

import pymongo
from beanie import Document, Indexed, before_event, after_event, DecimalAnnotation
import secrets
from beanie import Document, PydanticObjectId

from agent.models.base import GenericResponseModel
from agent.models.user_asset_list import UserAssetList
from agent.utils.common import get_unique_id, error_return, success_return, op_log


class UserAssetItemModel(BaseModel):
    uid: str
    mainchain: str
    token: str
    amount: str
    frozen: str


class UserAsset(Document):
    id: str = Field(default_factory=get_unique_id)
    uid: str
    mainchain: str = "BSC"
    token: str = "BNB"
    amount:  DecimalAnnotation = Field(decimal_places=8, default=0.00000000 )
    frozen:  DecimalAnnotation = Field(decimal_places=8, default=0.00000000 )

    create_at: datetime = datetime.now()
    update_at: datetime = datetime.now()

    @classmethod
    async def init_token(cls, uid, mainchain, token):
        vo = await cls.find_one({"uid": uid, 'mainchain': mainchain, "token": token})
        if vo:
            return vo
        else:
            item = await  UserAsset(id=get_unique_id(), uid=uid, mainchain=mainchain, token=token).save()
            return item

    def get_amount(self):
        return str((self.amount))

    def get_frozen(self):
        return str((self.frozen))

    @classmethod
    async def get_user_asset_list(cls, uid):
        return await cls.find({"uid": uid}).to_list()

    @classmethod
    async def get_user_asset_map(cls, uid):
        out = {}
        items = await cls.find({"uid": uid}).to_list()
        for item in items:
            out[item.token] = ((item.amount))
        return out

    @classmethod
    async def get_user_filter_asset_map(cls, where):
        out = {}
        items = await cls.find(where).to_list()
        for item in items:
            out[item.token] = ((item.amount))
        return out

    @classmethod
    async def incr(cls, uid: str, mainchain: str, token: str, amount: Decimal, op_type: str = "", desc: str = ""):
        vo = await cls.find_one({"uid": uid, "token": token,"mainchain":mainchain})
        if vo is None:
            await cls.init_token(uid, mainchain, token)
        if amount < 0:
            r = await cls.find_one({"uid": uid, "mainchain": mainchain,
                                    "token": token, "amount": {"$gte": amount * (-1)}}).update(
                {"$inc": {"amount": amount}})
        else:
            r = await cls.find_one({"uid": uid, "mainchain": mainchain, "token": token}).update(
                {"$inc": {"amount": amount}})
        i = r.modified_count
        print("incr->reuslt:", i,token,amount)

        if r.modified_count > 0:
            doc = {
                "uid": uid,
                "mainchain": mainchain,
                "token": token,
                "amount": amount,
                "op_type": op_type,
                "desc": desc
            }
            vo = await UserAssetList(**doc).create()
            return success_return({"id":vo.id})
        else:
            return error_return(1,"insufficent_balance",{"amount":amount})

    @classmethod
    async def withdraw(cls,uid,address,token,num,op_type="withdraw",desc="withdraw",mainchain="BSC"):
        print(token,num)
        ret = await cls.incr( uid, mainchain, token, Decimal(num) * (-1) , op_type, desc)
        if ret.code == 0:
            await UserWithdraw.add_withdraw(uid,address,mainchain,token,num,desc="user withdraw")
            return success_return(num)
        else:
            return error_return(1,ret.message)

    class Settings:
        name = "user_asset"
        indexes = [
            [
                ("address", pymongo.TEXT),
                ("uid", pymongo.ASCENDING)
            ],
        ]

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_schema_extra = {
            "example": {
                "uid": "1111",
                "address": "0xE91C299427D5DB24Dcc064db3Dc42d1bF1bf187E",
            }
        }



class UserCollectList(Document):
    id: str = Field(default_factory=get_unique_id)
    collect_id: int
    hash: Indexed(str, unique=True)
    status: int = 0
    amount:  DecimalAnnotation = Field(decimal_places=8, default=0.00000000 )
    token: str = ""
    address: str = ""
    to: str = ""
    msg: str = ""
    try_times: int = 0
    update_at: datetime = datetime.now()
    create_at: datetime = datetime.now()

    class Settings:
        name = "user_collect_list"
        indexes = [
            [
                ("uid", pymongo.ASCENDING)
            ],
        ]

    @classmethod
    async def save_tx(cls, hash, amount, token, address, dst,status):
        vo = await cls.find_one({"hash": hash})
        if vo:
            return vo
        else:
            collect_id = await get_next_id("collect_id")
            item = await UserCollectList(id=get_unique_id(), collect_id=collect_id, hash=hash, status=status,
                                          amount=Decimal(str(amount)), token=token, address=address, to=dst).save()
            return item




class UserWithdraw(Document):
    id: str = Field(default_factory=get_unique_id)
    uid: str
    withdraw_id:int=0
    mainchain: str
    token: str
    address: str
    amount:  DecimalAnnotation = Field(decimal_places=8, default=0.00000000 )
    status: Indexed(str)
    check_times:int=0
    hash: Indexed(str)=""
    src_id:str=""
    create_at: datetime = datetime.now()
    update_at: datetime = datetime.now()


    class Settings:
        name = "user_withdraw"
        indexes = [
            [
                ("address", pymongo.TEXT),
                ("uid", pymongo.ASCENDING)
            ],
        ]

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_schema_extra = {
            "example": {
                "uid": "1111",
                "address": "0xE91C299427D5DB24Dcc064db3Dc42d1bF1bf187E",
            }
        }

    @classmethod
    async def add_withdraw(cls,uid,address,mainchain,token,amount,desc="",status="waiting"):
        doc = {
            "withdraw_id":await get_next_id("withdraw"),
            "uid":uid,
            "mainchain":mainchain,
            "token":token,
            "amount":amount,
            "address":address,
            "desc":desc,
            "status":status
        }
        await cls(**doc).create()
        await op_log("提现:"+token+" ,"+amount+",{desc}",uid)
