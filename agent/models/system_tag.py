from typing import List

from beanie import Document
from pydantic import Field

from agent.utils.common import get_unique_id

from pydantic import BaseModel, Field
from beanie.odm.operators.find.logical import Or,BaseFindLogicalOperator
from beanie.odm.operators.find.comparison import In
class SystemTag(Document):
    id:str=Field(default_factory=get_unique_id)
    title: str
    value: str
    tag: str
    num: int=1

    @classmethod
    async def filter_tags(self, ids):
        objects = await self.find({}).to_list()
        my_map = {obj.id:obj for obj in objects}
        return [id for id in ids if id in my_map]
    @classmethod
    async def get_tags(cls, ids:List=[]):
        if len(ids)>0:
            filter = {"id":In(cls.id, ids)}
        else:
            filter = {}
        objects = await cls.find(filter).to_list()
        return [{"id":obj.id,"title":obj.title,"value":obj.value,"tag":obj.tag} for obj in objects]
    class Settings:
        name = "system_tag"

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

class SystemtTagModel(BaseModel):
    id:str=""
    title: str=""
    value: str=""
    tag:str=""
    class Config:
        json_schema_extra = {
            "example": {
                "id":"id",
                "title": "tag",
                "value": "name",
                "tag":"NFT",
            }
        }
