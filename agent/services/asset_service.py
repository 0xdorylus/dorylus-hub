from typing import List

from agent.models.user_asset import UserAsset, UserAssetItemModel

from agent.config import CONFIG
class AssetService:
    llm: None

    async def get_deposit_address(self,mainchain,uid):
        address = await UserAsset.get_deposit_address(uid,mainchain)
        return address


    @classmethod
    async def init_asset(cls):
        assets = CONFIG.token_list
        print(assets)

    @classmethod
    async def get_supported_asset_list(cls):
        assets = CONFIG.deposit_token_list
        print(assets)
        return assets

    @classmethod
    async def init_user_asset(cls,uid)->List[UserAssetItemModel]:
        token_list = CONFIG.token_list
        mainchain = CONFIG.mainchain
        items : List[UserAssetItemModel]=[]

        for token in token_list:
            vo = await UserAsset.init_token(uid,mainchain,token)

            item = UserAssetItemModel(
                uid=vo.uid,
                token=vo.token,
                mainchain=vo.mainchain,
                amount=vo.get_amount(),
                frozen=vo.get_frozen()
            )
            items.append(item)
        return items
    @classmethod
    async def get_user_asset_list(cls,uid)->List[UserAssetItemModel]:
        items : List[UserAssetItemModel]=[]
        asset_list = await UserAsset.get_user_asset_list(uid)
        for vo in asset_list:
            item = UserAssetItemModel(
                uid=vo.uid,
                token=vo.token,
                mainchain=vo.mainchain,
                amount=vo.get_amount(),
                frozen=vo.get_frozen()
            )
            items.append(item)
        return items




