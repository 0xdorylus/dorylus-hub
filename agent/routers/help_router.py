import math
from typing import List

from fastapi import APIRouter, Depends, Response, HTTPException

from agent.models.assistant import AssistantModel, Assistant, CreateAssistantModel
from agent.models.base import GenericResponseModel
from agent.models.feedback import FeedbackRequestModel, Feedback, FeedbackItemModel, FeedbackListModel, FeedbackIdModel
from agent.models.request_response_model import FinishResponseModel, PageRequestModel
from agent.models.user import User
from agent.services.acl_service import AclService
from agent.services.assistant_service import AssistantService
from agent.utils.x_auth import get_uid_by_token
from agent.models.subscribe import Subscription

router = APIRouter(prefix="/help", tags=["help"])


@router.post("/add_feedback", response_model=GenericResponseModel)
async def add_feedback(form: FeedbackRequestModel, uid: str = Depends(get_uid_by_token)):
    """
    添加反馈
    """
    data = form.model_dump()
    data['uid'] = uid
    await Feedback(**data).create()
    return GenericResponseModel()


@router.post("/del_feedback", response_model=GenericResponseModel)
async def del_feedback(form: FeedbackIdModel, acl_service: AclService = Depends(),
                       uid: str = Depends(get_uid_by_token)):
    """
    删除反馈
    """
    if not acl_service.user_can_list_feedback(uid):
        raise HTTPException(403, "Forbidden")

    await Feedback.find(Feedback.id == form.id).delete()

    return GenericResponseModel()


@router.post("/list", response_model=GenericResponseModel[FeedbackListModel])
async def list_feedback(form: PageRequestModel, acl_service: AclService = Depends(),
                        uid: str = Depends(get_uid_by_token)):
    """
    反馈列表
    """
    if not acl_service.user_can_list_feedback(uid):
        raise HTTPException(403, "Forbidden")

    skip = (form.page - 1) * form.pagesize

    limit = form.pagesize
    items: List[FeedbackItemModel] = []

    sort = (-Feedback.id)
    filter = {}

    total = await Feedback.find(filter).count()

    total_page = math.ceil(total / form.pagesize)

    objects = await Feedback.find(filter).sort(sort).skip(skip).limit(limit).to_list()
    for item in objects:
        object = FeedbackItemModel(**item.dict())
        items.append(object)

    response_model = FeedbackListModel(total=total, list=items, total_page=total_page)
    return GenericResponseModel(result=response_model)
