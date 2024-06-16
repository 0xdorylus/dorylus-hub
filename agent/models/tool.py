import json
from datetime import datetime
from typing import Optional,List

from pydantic import BaseModel, Field
from beanie import Document

from agent.models.base import BaseDocument
from agent.utils.common import get_unique_id, get_current_time


class ParametersModel(BaseModel):
    name: str
    description: str
    required: Optional[bool] = True


class ToolModel(BaseModel):
    id:str
    name: str
    description: str

    parameters: List[ParametersModel]
    icon:Optional[str]=""
    pic_list:Optional[List]=[]
    trigger_list:Optional[List]=[]
    create_at: int = get_current_time()

class Tool(Document):
    id: str=Field(default_factory=get_unique_id)
    name: str = 'tool'
    description: str = 'This is a tool that ...'
    parameters: list = []
    icon:Optional[str]=""
    tag:List[str]=[]
    pic_list:Optional[List]=[]
    trigger_list:Optional[List]=[]
    enabled: bool = False
    create_at: int = get_current_time()
    update_at: int = get_current_time()


    class Settings:
        name = "tool"

