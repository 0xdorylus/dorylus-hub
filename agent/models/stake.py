import logging

from bson import Decimal128
from pydantic import BaseModel, Field
from datetime import datetime
from ipaddress import IPv4Address
from typing import Optional, List, Set, Annotated
from beanie import DecimalAnnotation, Document
from decimal import Decimal
import pymongo
from beanie import Document, Indexed, before_event, after_event
from pymongo import IndexModel

from agent.models.stake_list import StakeList
from agent.models.user_asset import UserAsset
from agent.utils.common import get_unique_id, error_return, encode_input
from agent.utils.common import op_log
from agent.utils.common import success_return
from fastapi import Depends, HTTPException, status
from agent.models.request_response_model import UserInfoModel, UserDetailModel
class Stake(Document):
    id: str = Field(default_factory=get_unique_id)
    uid: str
    mainchain: str = "BSC"
    token: str = "SCORE"
    amount: Annotated[DecimalAnnotation, Field("0.000000")]

    frozen: Decimal128 = Decimal128("0.000000")
    create_at: datetime = datetime.now()
    update_at: datetime = datetime.now()
    class Settings:
        name = "stake"
        indexes = [
            IndexModel(
                [
                    ("uid", pymongo.ASCENDING),
                    ("token", pymongo.DESCENDING),
                ],
                name="uid_token_index_DESCENDING",
            ),
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
    async def init_token(cls, uid, mainchain, token):
        vo = await cls.find_one({"uid": uid, 'mainchain': mainchain, "token": token})
        if vo:
            return vo
        else:
            item = await  Stake(id=get_unique_id(),uid=uid, mainchain=mainchain, token=token,amount=Decimal128("0.000000"),frozen=Decimal128("0.000000")).save()
            return item

    @classmethod
    async def get_user_filter_asset_map(cls, where):
        out = {}
        items = await cls.find(where).to_list()
        for item in items:
            out[item.token] = item.amount
        return out

    @classmethod
    async def incr(cls, uid: str, mainchain: str,token:str,amount:Decimal,op_type:str="",desc:str=""):
        vo = await cls.find_one({"uid":uid,"token":token})
        if vo is None:
            await cls.init_token(uid, mainchain, token)
        print("asset num:",vo)
        if amount<0:
            r = await cls.find_one({"uid": uid, "mainchain": mainchain,
                                "token": token,"amount":{"$gte":amount *(-1)}}).update({"$inc":{"amount":amount}})
        else:
            r = await cls.find_one({"uid": uid, "mainchain": mainchain, "token":token}).update({"$inc":{"amount":amount}})
        i = r.modified_count
        print("incr->reuslt:",i)

        if r.modified_count>0:
            doc = {
                "uid":uid,
                "mainchain": mainchain,
                "token": token,
                "amount": amount,
                "op_type":op_type,
                "desc": desc
            }
            vo = await StakeList(**doc).create()
            return success_return({"id":vo.id})
        else:
            return error_return(1,"balance_insufficent")



    @classmethod
    async def try_stake(cls,uid: str, token: str, num:float):
        if num < 0:
            return error_return(1,"num_invalid",num)
        ret = await UserAsset.incr(uid, "BSC",token, Decimal(num)*(-1), "stake", "抵押")
        if ret.code == 0:
            op_type = "stake"
            desc = "stake"
            await cls.incr(uid, "BSC",token,Decimal(num),op_type,desc)
            return success_return({token:token,num:num})
        else:
            return ret

    @classmethod
    async def try_unstake(cls,uid: str,  token: str, num:float):
        if num < 0:
            return error_return(1, "num_invalid", num)
        op_type = "unstake"
        desc = "unstake"
        ret  = await cls.incr(uid, "BSC", token, num * (-1), op_type, desc)

        if ret.code == 0:
            await UserAsset.incr(uid, "BSC", token, Decimal(num), "unstake", "解押")
            return success_return(num)
        else:
            return error_return(1,"balance_insufficient",num)

