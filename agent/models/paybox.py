import logging

from bson import ObjectId
from pydantic import BaseModel, Field
from datetime import datetime
from ipaddress import IPv4Address
from typing import Optional, List, Set

import pymongo
from beanie import Document, Indexed, before_event, after_event

from agent.utils.common import get_unique_id, error_return, encode_input
from agent.utils.common import op_log
from agent.utils.common import success_return
from fastapi import Depends, HTTPException, status
from agent.models.request_response_model import UserInfoModel, UserDetailModel

"""
## 必要条件

1. 注册 nabox DID 账户。
2. 提供交易到账通知回调URL。

## 名词释义约定

业务系统：指对接 paybox 的应用系统

paybox：指 paybox 跨链支付收款系统

商户：指业务系统在 paybox 中注册的一个收款主体

用户：指业务系统的用户

支付链：指用户在发起转账交易的区块链网络

支付资产：指用户在支付链转账交易支付的资产

收款链：指商户获得用户支付资产兑换成 USDT 后接收资产的区块链网络

收款地址：指商户在注册 nabox DID 时使用的区块链地址

## 业务流程

1. 业务系统创建支付订单号。
2. 换起 paybox 支付页，传入订单号、收款金额、支付链等信息。
3. 用户在 paybox 支付页完成转账交易发送。
4. paybox 完成资产跨链兑换。
5. paybox 通过提供的通知URL 通知业务系统交易已完成。
6. 业务系统可通过查询接口查询交易订单信息。
"""
class CreatePayOrder(BaseModel):
    token: str
    num: float
    memo:str=""

class Coin(BaseModel):
    symbol:str
    decimal:int
    cent:str
    amount:str

class PayboxOrderModel(BaseModel):
    outerOrderNo:str
    orderNo:str
    fromTxHash:str
    fromAmount:Coin
    fromAddress:str
    fromChain:str
    toAmount:Coin
    payeeFee:Coin
    toTxHash:str
    toAddress:str
    fromTimestamp:int
    toTimestamp:int
    sign:str
    sendTime:int

class PayOrderCallback(Document):
    id: str = Field(default_factory=get_unique_id)
    outerOrderNo:str
    orderNo:str
    fromTxHash:str
    fromAmount:Coin
    fromAddress:str
    fromChain:str
    toAmount:Coin
    payeeFee:Coin
    toTxHash:str
    toAddress:str
    fromTimestamp:int
    toTimestamp:int

    create_at: datetime = datetime.now()
    update_at: datetime = datetime.now()

    class Settings:
        name = "pay_order_callback"

class PayOrder(Document):
    id: str = Field(default_factory=get_unique_id)
    uid:str
    token:str
    num:float
    hash:str=""
    status:str="prepare"
    memo:str=""


    create_at: datetime = datetime.now()
    update_at: datetime = datetime.now()

    class Settings:
        name = "pay_order"
    @classmethod
    async def create_order(cls,uid,form:CreatePayOrder):
        doc = form.model_dump()
        doc['uid']=uid
        order = await cls(**doc).create()
        return order.id

