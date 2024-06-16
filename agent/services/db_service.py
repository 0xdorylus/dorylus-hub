from typing import List

from agent.models.user_asset import UserAsset, UserAssetItemModel

from agent.config import CONFIG


def singleton(cls):
    instances = {}

    def wrapper(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return wrapper

@singleton
class DBService:
    llm: None
    def __init__(self):
        print("init")




    @classmethod
    async def get_next(cls, name):
        # return await get_next_id(name)
        print("next",name)

        return 1



