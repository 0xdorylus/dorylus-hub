import math
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, Response, HTTPException

from agent.models.assistant import AssistantModel, Assistant, CreateAssistantModel
from agent.models.base import GenericResponseModel
from agent.models.feedback import FeedbackRequestModel, Feedback, FeedbackItemModel, FeedbackListModel, FeedbackIdModel
from agent.models.luck import LotteryRequestModel, Lottery, LotteryJoinModel, LotteryUser, LotteryItemModel, \
    LotteryListModel, LotteryDetailModel, LotteryUserrListModel, LotteryUserItem, LotteryUserPageRequestModel
from agent.models.request_response_model import FinishResponseModel, PageRequestModel, IDModel
from agent.models.user import User
from agent.services.acl_service import AclService
from agent.services.assistant_service import AssistantService
from agent.utils.x_auth import get_uid_by_token
from agent.models.subscribe import Subscription

router = APIRouter(prefix="/lottery", tags=["lottery"])


@router.post("/upsert_lottery", response_model=GenericResponseModel,summary="添加修改抽奖")
async def upsert_lottery(form: LotteryRequestModel, uid: str = Depends(get_uid_by_token)):
    """
    id
    """
    if form.num<1:
        return GenericResponseModel(cdoe=1,message="Num must bigger thant 1")
    if form.id == "":
        data = form.model_dump()
        data['uid'] = uid
        del data['id']
        lotterry = await Lottery(**data).create()
        return GenericResponseModel(reuslt=lotterry)
    else:
        data = {k: v for k, v in form.items() if v is not None and v != "" and v != []}
        data['update_at'] = datetime.now()
        update = {"$set": data}
        lotterry = await Lottery().find_one({"_id":form.id,"uid":uid}).update(update)
        return GenericResponseModel(reuslt=lotterry)

@router.post("/start_lucky_time", response_model=GenericResponseModel,summary="开启抽奖")
async def start_lucky_time(form: IDModel, acl_service: AclService = Depends(),
                       uid: str = Depends(get_uid_by_token)):
    """
    馈
    """
    lottery = await Lottery.find_one({"_id":form.id,"uid":uid,"status":"pending"})
    if lottery and lottery.uid == uid:
        await Lottery.start_lucky_time(form.id,uid)
        return GenericResponseModel()
    else:
        return GenericResponseModel(code=1,message="error")


@router.post("/join", response_model=GenericResponseModel)
async def join(form: LotteryJoinModel,
                       uid: str = Depends(get_uid_by_token)):
    """
    馈
    """
    lottery = await Lottery.find_one({"_id":form.id,"status":"pending"})
    if lottery and lottery.code == form.code:
        vo = await LotteryUser.find_one({ "luck_id":lottery.id,"uid":uid})
        if vo:
            return GenericResponseModel(code=1,message="already_joined")

        doc = {
            "uid":uid,
            "luck_id":lottery.id
        }
        await LotteryUser(**doc).create()
        return GenericResponseModel()
    else:
        return GenericResponseModel(code=1,message="Lucky Code error")


@router.post("/list_lottery", response_model=GenericResponseModel[LotteryListModel])
async def list_lottery(form: PageRequestModel,
                        uid: str = Depends(get_uid_by_token)):
    """
    抽奖活动列表
    """


    skip = (form.page - 1) * form.pagesize

    limit = form.pagesize
    items: List[LotteryItemModel] = []

    sort = (-Feedback.id)
    filter = {}

    total = await Lottery.find(filter).count()

    total_page = math.ceil(total / form.pagesize)

    objects = await Lottery.find(filter).sort(sort).skip(skip).limit(limit).to_list()
    for item in objects:
        object = LotteryItemModel(**item.dict())
        items.append(object)

    response_model = LotteryListModel(total=total, list=items, total_page=total_page)
    return GenericResponseModel(result=response_model)



@router.post("/view_lottery", response_model=GenericResponseModel[LotteryDetailModel])
async def view_lottery(form: IDModel,
                        uid: str = Depends(get_uid_by_token)):
    """
    抽奖活动
    """
    lottery = await Lottery.get(form.id)
    if lottery:
        response_model = LotteryDetailModel(**lottery.model_dump())
        if lottery.uid == uid:
            response_model.is_admin = True

        return GenericResponseModel(result=response_model)
    else:
        return GenericResponseModel(code=404,message="Not Found")


@router.post("/list_joined_users", response_model=GenericResponseModel[LotteryUserrListModel])
async def list_joined_users(form: LotteryUserPageRequestModel,
                        uid: str = Depends(get_uid_by_token)):
    """
    参加抽奖活动的用户列表
    """


    skip = (form.page - 1) * form.pagesize

    limit = form.pagesize
    items: List[LotteryUserItem] = []

    sort = (-LotteryUser.id)
    filter = {"luck_id":form.id}

    total = await LotteryUser.find(filter).count()

    total_page = math.ceil(total / form.pagesize)

    objects = await LotteryUser.find(filter).sort(sort).skip(skip).limit(limit).to_list()
    for item in objects:
        object = LotteryUserItem(**item.dict())
        object.user = await User.get_info(object.uid)
        if object.user.username:
            object.user.username =  object.user.username[:6]+"..."+  object.user.username[-6:]
        items.append(object)

    response_model = LotteryUserrListModel(total=total, list=items, total_page=total_page)
    return GenericResponseModel(result=response_model)
