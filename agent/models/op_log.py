import json
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field
from beanie import Document

class OpLog(Document):
    msg: str
    uid:str
    extra: str
    create_at: datetime = datetime.now()

    @classmethod
    async def record(cls,msg,uid:str(""),extra={}):
        data = {
            "uid":uid,
            "msg":msg,
            "extra":json.dumps(extra)
        }
        await OpLog(**data).create()

    class Settings:
        name = "oplog"

    class Config:
        json_schema_extra = {
            "example": {
                "uid": "bots001",
                "msg": "0xE91C299427D5DB24Dcc064db3Dc42d1bF1bf187E",
                "extra": "",

            }
        }
