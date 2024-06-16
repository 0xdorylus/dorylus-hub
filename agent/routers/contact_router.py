import math
from typing import List

from fastapi import APIRouter, Depends, Response, HTTPException

from agent.models.base import GenericResponseModel
from agent.models.contact import ContactItemModel, ContactListItemModel, ContactListResponseModel
from agent.models.request_response_model import FinishResponseModel, IDModel, PageRequestModel, GeneralRequestModel
from agent.models.token_gate import TokenGateItemModel, TokenGate
from agent.models.contact import Contact
from agent.utils.common import success_return
from agent.utils.x_auth import get_uid_by_token

router = APIRouter(prefix="/contact", tags=["contact"])

from pydantic import BaseModel


class ContactMemoModel(BaseModel):
    memo: str
    id: str


@router.post("/set_memo", response_model=GenericResponseModel, summary="添加修改联系人")
async def set_memo(form: ContactMemoModel, uid: str = Depends(get_uid_by_token)):
    """
    """
    await Contact.find_one({"receiver": form.id, "uid": uid}).update({"$set": {"memo": form.memo}})
    return success_return()


@router.post("/upsert_contact", response_model=GenericResponseModel, summary="添加修改联系人")
async def upsert_contact(form: ContactItemModel, uid: str = Depends(get_uid_by_token)):
    """
        有ID就是修改，没有ID就是添加
    """
    return await Contact.upsert(uid, form)


@router.post("/list_contact_item", response_model=GenericResponseModel[ContactListResponseModel], summary="联系人列表")
async def list_contact_item(request_form: PageRequestModel, uid: str = Depends(get_uid_by_token)):
    """
        联系人列表
    """
    skip = (request_form.page - 1) * request_form.pagesize

    limit = request_form.pagesize
    items: List[ContactListItemModel] = []

    filter = {"uid": uid}
    sort = []

    total = await Contact.find(filter).count()

    total_page = math.ceil(total / request_form.pagesize)

    objects = await Contact.find(filter).sort(sort).skip(skip).limit(limit).to_list()
    for item in objects:
        vo = ContactListItemModel(**item.dict())
        user = {
            "id": item.receiver,
            "username": item.username,
            "avatar": item.avatar,
        }
        vo.user = user
        items.append(vo)

    response_model = ContactListResponseModel()
    response_model.total = total
    response_model.list = items
    response_model.total_page = total_page
    return GenericResponseModel(result=response_model)


