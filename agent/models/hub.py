from pydantic import BaseModel, Field
from beanie import Document, PydanticObjectId
from datetime import datetime
from agent.utils.common import get_unique_id
from pydantic import BaseModel, Field

class RegisterAgent(Document):
    id:str=Field(default_factory=get_unique_id)
    agent_id: str
    name: str
    pubkey: str = None
    status: int = 0
    score: int = 0
    description: str = None
    health: int = 1
    create_at: datetime = datetime.now()
    update_at: datetime = datetime.now()
    class Config:
        json_schema_extra = {
            "example": {
                "agent_id": "1",
                "target_uid": "100",
                "name": "bots001",
                "pubkey":"xxx"

            }
        }