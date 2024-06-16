from agent.models.user_asset import UserAsset


class BlockService:
    def __init__(self):
        pass


    async def get_deposit_address(self,mainchain:str, uid: str):
        userAsset = await UserAsset.find_one(UserAsset.uid==uid,UserAsset.mainchain==mainchain)
        pass

    @classmethod
    async def create_did(cls,uid):
        pass

    @classmethod
    async def sign_message(cls,uid):
        pass