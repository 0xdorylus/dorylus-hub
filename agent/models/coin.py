import pymongo
from beanie import Document
from bson import ObjectId, Decimal128
from agent.utils.common import get_unique_id
from pydantic import BaseModel, Field

class Coin(Document):
    id:str=Field(default_factory=get_unique_id)
    symbol:str=""
    decimal: int
    cent:  Decimal128 = Decimal128("0.000000")
    amount: Decimal128 = Decimal128("0.000000")
