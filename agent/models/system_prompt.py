from typing import List, Optional

from beanie import Document
from pydantic import Field
from datetime import datetime
from agent.models.base import BaseDocument
from agent.utils.common import get_unique_id

from pydantic import BaseModel, Field
from beanie.odm.operators.find.logical import Or,BaseFindLogicalOperator
from beanie.odm.operators.find.comparison import In


class SystemtPromptForm(BaseModel):
    name: str
    name_zh: Optional[str] =  ""
    prompt: str
    tag: Optional[str] =  ""
    model: Optional[str] =  ""
    org: Optional[str] =  "openai"
    description: Optional[str] =  ""
    icon: Optional[str] =  ""

    # class Config:
    #     json_schema_extra = {
    #         "example": {
    #             "title": "tag",
    #             "value": "name",
    #             "tag":"NFT",
    #         }
    #     }


class SystemPrompt(Document):
    id:str=Field(default_factory=get_unique_id)
    name: str
    name_zh: Optional[str] =  ""
    prompt: str
    uid: Optional[str] =  ""
    tag: Optional[str] =  ""
    model: Optional[str] =  ""
    description: Optional[str] =  ""
    icon: Optional[str] =  ""

    org: Optional[str] =  "openai"
    created_at:datetime = datetime.now()
    updated_at:datetime = datetime.now()


    class Settings:
        name = "system_prompt"

    @classmethod
    async def get_system_prompt(cls,id):
        object = await cls.get(id)
        if object:
            return object.prompt
        else:
            return None
