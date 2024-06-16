import asyncio

from pydantic import BaseModel
from typing import Generic
from beanie import Document
import math
from typing import TypeVar

T = TypeVar('T')


class GenericResponseModel(BaseModel, Generic[T]):
    code: int = 0
    message: str = ""
    result: T = None


class BaseDocument(Document):

    @classmethod
    async def get_page(cls, query=None, options={"page": 1, "pagesize": 10, "sort": {"_id": -1}}, callback=None,
                       is_async_callback=False):
        if query is None:
            query = {}
        if options['page'] < 1:
            options['page'] = 1
        if options['pagesize'] < 10:
            options['pagesize'] = 10

        skip = (options['page'] - 1) * options['pagesize']
        limit = options['pagesize']
        sort = options['sort']

        total = await cls.find(query).count()
        total_page = math.ceil(total / options['pagesize'])

        objects = await cls.find(query).sort(sort).skip(skip).limit(limit).to_list()
        if callback is not None:
            if is_async_callback:
                objects = await asyncio.gather(*[callback(obj) for obj in objects])
            else:
                objects = list(map(callback, objects))

        out = {
            "total": total,
            "total_page": total_page,
            "list": objects
        }
        return GenericResponseModel(result=out)
