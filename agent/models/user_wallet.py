import base64
import logging

from bson import ObjectId, Decimal128
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from ipaddress import IPv4Address
from decimal import Decimal

import pymongo
from beanie import Document, Indexed, before_event, after_event
import secrets
from beanie import Document, PydanticObjectId
from beanie import Insert

from agent.utils.common import get_unique_id, aes_256_decrypt, get_current_time

from eth_account import Account

from agent.utils.common  import aes_256_encrypt
import binascii
from agent.config import CONFIG
class UserWalletItemModel(BaseModel):
    uid: str
    mainchain: str
    address: str



class UserWallet(Document):
    id: str = Field(default_factory=get_unique_id)
    uid: str
    mainchain: str
    address: str
    private_key:str=""
    create_at: int = get_current_time()
    update_at: int = get_current_time()

    @classmethod
    async def get_key(cls,address):
        address = address.lower()
        vo = await cls.find_one({"address": address})
        if vo:
            s_bytes = CONFIG.db_save_key.encode()
            private_key_str=vo.private_key
            data = base64.b64decode(private_key_str)
            s = aes_256_decrypt(s_bytes, data)
            hex_data = binascii.hexlify(s).decode('utf-8')
            return hex_data
        else:
            return None

    @classmethod
    async def get_user_wallet(cls, uid, mainchain):
        vo = await cls.find_one({"uid": uid, 'mainchain': mainchain})
        if vo:
            return UserWalletItemModel(**vo.model_dump())
        else:
            acct = Account.create()
            # print(acct.key)
            # print(acct.key.decode('latin-1'))

            s_bytes = CONFIG.db_save_key.encode()
            private_key_bytes = aes_256_encrypt(s_bytes,acct.key)
            private_key_str = base64.b64encode(private_key_bytes)


            doc = {
                "uid":uid,
                "mainchain":mainchain,
                "address":acct.address.lower(),
                "private_key":private_key_str
            }
            item = await  UserWallet(**doc).save()
            return UserWalletItemModel(**item.model_dump())

    def get_amount(self):
        return str((self.amount))
    def get_frozen(self):
        return str((self.frozen))
    @classmethod
    async def get_user_asset_list(cls, uid):
        return await cls.find({"uid": uid}).to_list()

    @classmethod
    async def get_uid_by_address(cls, address: str):
        vo = await cls.find_one({"address": address})
        if vo:
            return vo.uid
        else:
            return None


    @classmethod
    async def get_deposit_address(cls, uid: str, mainchain: str):
        vo = await cls.find_one({"uid": uid, "mainchain": mainchain})
        if vo:
            return vo.address
        else:
            items = await cls.get_user_wallet( uid, mainchain)
            return items.address

    class Settings:
        name = "user_wallet"
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
