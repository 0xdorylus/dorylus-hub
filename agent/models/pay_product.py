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


class PayConfirmItem(BaseModel):
    order_id: str=""
    ticket: str=""
class PayProductItem(BaseModel):
    id: str=""
    product_id: str=""
    price: float=0
    days: int=0
    desc: str=""
    title: str=""
    promote: str=""
class PayProduct(Document):
    id: str = Field(default_factory=get_unique_id)
    product_id: str
    price: float=0.0
    days: int=3
    desc: str=""
    title: str=""
    promote: str=""

    create_at: datetime = datetime.now()
    update_at: datetime = datetime.now()

    class Settings:
        name = "pay_product"
