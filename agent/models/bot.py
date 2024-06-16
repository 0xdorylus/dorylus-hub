from beanie import Document
from pydantic import Field

from agent.models.base import BaseDocument
from agent.utils.common import get_unique_id

from pydantic import BaseModel, Field

class Bot(BaseDocument):
    id:str=Field(default_factory=get_unique_id)
    title: str
    value: str
    tag: str
    num: int=1

    class Settings:
        name = "bot"

        # indexes = [
        #     [
        #         ("address", pymongo.TEXT),
        #         ("username", pymongo.TEXT),
        #         ("invite_code", pymongo.TEXT),
        #         ("email", pymongo.TEXT),
        #         ("uid",pymongo.ASCENDING)
        #     ],
        # ]

    class Config:
        json_schema_extra = {
            "example": {
                "title": "tag",
                "value": "name",
            }
        }




class SystemtTagForm(BaseModel):
    title: str
    value: str
    tag:str
    class Config:
        json_schema_extra = {
            "example": {
                "title": "tag",
                "value": "name",
                "tag":"NFT",
            }
        }

