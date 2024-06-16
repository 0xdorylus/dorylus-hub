import logging

from bson import ObjectId
from pydantic import BaseModel, Field
from datetime import datetime
from ipaddress import IPv4Address
from typing import Optional, List, Set

import pymongo
from beanie import Document, Indexed, before_event, after_event

from agent.models.user_asset import UserAsset
from agent.utils.common import get_unique_id, error_return, encode_input
from agent.utils.common import op_log
from agent.utils.common import success_return
from fastapi import Depends, HTTPException, status
from agent.models.request_response_model import UserInfoModel, UserDetailModel
class ServerNode(Document):
    id: str = Field(default_factory=get_unique_id)
    uid: str
    token: str
    status: int = 0
    num: float = 0
    expire_at: datetime = datetime.now()
    create_at: datetime = datetime.now()
    update_at: datetime = datetime.now()
    class Settings:
        name = "server_node"

