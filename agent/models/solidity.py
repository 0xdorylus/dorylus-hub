from datetime import datetime

import pymongo
from beanie import Document
from bson import ObjectId

from agent.models.file_meta import SoldityFileMeta
from agent.utils.common import get_unique_id
from pydantic import BaseModel, Field

class DeployedContract(Document):
    id:str=Field(default_factory=get_unique_id)
    uid:str
    deploy_tx:str=None
    status:int=0
    contract:str=None
    abi:str=None
    mainchain:str=None
    solidity_file: SoldityFileMeta=None
    error:str=None
    created_at:datetime = datetime.now()
    updated_at:datetime = datetime.now()

    class Settings:
        name = "deployed_contract"

        indexes = [
            [
                ("contract", pymongo.TEXT),

            ],
        ]
    class Config:
        json_schema_extra = {
            "example": {
                "filename": "bots001",
                "sz": "0xE91C299427D5DB24Dcc064db3Dc42d1bF1bf187E",
            }
        }