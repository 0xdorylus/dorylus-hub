import pymongo
from beanie import Document
from bson import ObjectId
from agent.utils.common import get_unique_id
from pydantic import BaseModel, Field
class FileMetaInfo(BaseModel):
    id:str=""
    uid:str=""
    filehash: str=""
    filename: str
    size: int=0

class FileMetadata(Document):
    id:str=Field(default_factory=get_unique_id)
    uid:str=""
    filehash: str=""
    filename: str
    size: int=0
    content_type: str
    filepath:str=""
    file_ext:str=""
    status:int=0
    url:str=""

    class Settings:
        name = "fs"

        # indexes = [
        #     [
        #         ("filehash", pymongo.TEXT),
        #
        #     ],
        # ]
    class Config:
        json_schema_extra = {
            "example": {
                "filename": "bots001",
                "size": 100,
                "content_type":"image/png",

            }
        }
#
class SoldityFileMeta(FileMetadata):

    abi: str = ""
    bytecode: str = ""
    spec: str = ""
    error: str = ""
    version: str=""
    contract_name:str=""
    deploy_tx:str=""
    contract:str=""
    class Settings:
        name = "fs_solidity"

        indexes = [
            [
                ("filehash", pymongo.TEXT),

            ],
        ]

    class Config:
        json_schema_extra = {
            "example": {
                "filename": "bots001",
                "size": "0xE91C299427D5DB24Dcc064db3Dc42d1bF1bf187E",
            }
        }