from beanie import Document
from pydantic import Field
from pymongo.database import Database

class Counter(Document):
    type: str = Field(default="counter")
    seq: int = Field(default=1)
    async def increment(self):
        self.seq += 1
        await self.update()

    @classmethod
    async def get_seq(cls,name):
        query = {type: name}
        updated_doc = await cls.find(cls.type == name).inc({cls.seq: 1})
        print(updated_doc)

        return updated_doc['seq']


