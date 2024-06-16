from typing import List

from fastapi import APIRouter, Depends, Response, HTTPException

from agent.models.assistant import AssistantModel, Assistant, CreateAssistantModel
from agent.models.base import GenericResponseModel
from agent.models.knowledge import TrainFileDataModel
from agent.models.request_response_model import UploadResponseModel
from agent.models.user_acheievements import AchievementItem, Achievement, UserAchievement, UserAchievementItem, \
    UserAchievementRequestItem
from agent.models.user_asset import UserAssetItemModel
from agent.models.user_wallet import UserWallet, UserWalletItemModel
from agent.services.acl_service import AclService
from agent.services.asset_service import AssetService
from agent.services.assistant_service import AssistantService
from agent.services.fs_service import FsService
from agent.utils.common import filter_empty_value
from agent.utils.x_auth import get_uid_by_token
from agent.models.subscribe import Subscription

router = APIRouter(prefix="/achieve", tags=["achieve"])


@router.post("/upsert_achieve_item", response_model=GenericResponseModel[AchievementItem],
             summary="初始化系统的成就配置")
async def upsert_achieve_item(form: AchievementItem, acl_service: AclService = Depends(),
                              uid: str = Depends(get_uid_by_token)):
    """
        初始化系统的成就配置
    """
    if acl_service.user_can_create_agent(uid):

        if form.id:
            data = filter_empty_value(form)
            update_query = {"$set": data}
            item = await  AchievementItem.find_one(AchievementItem.id == form.id).update(update_query)
        else:
            del form.id
            data = form.model_dump()
            item = await AchievementItem(**data).create()
        return GenericResponseModel(result=item)
    else:
        raise HTTPException(403, "Can't Create")


@router.post("/upsert_user_achieve_item", response_model=GenericResponseModel[UserAchievement], summary="用户成就模拟")
async def upsert_user_achieve_item(form: UserAchievementRequestItem, acl_service: AclService = Depends(),
                                   uid: str = Depends(get_uid_by_token)):
    """
        初始化用户成就
    """
    if acl_service.user_can_create_agent(uid):
        achieve_id = form.achieve_id
        achieve = await Achievement.get(achieve_id)
        if not achieve:
            raise HTTPException(404, "achieve_not_found")

        if form.id:
            data = filter_empty_value(form)
            del data['achieve_id']
            update_query = {"$set": data}
            item = await UserAchievement.find_one(AchievementItem.id == form.id).update(update_query)
        else:
            data = achieve.model_dump()
            data['uid'] = uid
            data['achieve_id'] = achieve_id
            data['num'] = form.num
            print(data)

            item = await UserAchievement(**data).create()
        return GenericResponseModel(result=item)
    else:
        raise HTTPException(403, "Can't Create")


@router.get("/get_acheive_item_list", response_model=GenericResponseModel[List[AchievementItem]], summary="成就勋章列表")
async def get_acheive_item_list():
    """
        成就勋章列表
    """
    outs: List[AchievementItem] = []
    items = await Achievement.find_all().to_list()
    for item in items:
        outs.append(AchievementItem(**item.model_dump()))
    return GenericResponseModel(result= outs)


@router.get("/get_user_acheive_item_list", response_model=GenericResponseModel[List[UserAchievementItem]], summary="用户的成就勋章列表")
async def get_user_acheive_item_list(uid: str = Depends(get_uid_by_token)):
    """
        用户的成就勋章列表
    """
    outs: List[UserAchievementItem] = []
    items = await Achievement.find_all().to_list()
    for item in items:
        user_item = await UserAchievement.find_one(UserAchievement.achieve_id == item.id, UserAchievement.uid == uid)
        if user_item:
            data = UserAchievementItem(
                id=user_item.id,
                uid=uid,
                tag=item.tag,
                logo=item.logo,
                nft_id=item.logo,
                contract=item.logo,
                chain=item.logo,
                intro=item.logo,
                limit_num=item.limit_num,
                user_num=user_item.num
            )
            outs.append(data)
        else:
            data = item.model_dump()
            data['uid'] = uid;
            data['user_num'] = 0;
            outs.append(UserAchievementItem(**data))
    return GenericResponseModel(result=outs)
