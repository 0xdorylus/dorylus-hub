from typing import List

from fastapi import APIRouter, Depends, Response, HTTPException

from agent.models.base import GenericResponseModel
from agent.models.request_response_model import FinishResponseModel, IDModel
from agent.models.token_gate import TokenGateItemModel, TokenGate
from agent.utils.x_auth import get_uid_by_token

router = APIRouter(prefix="/search", tags=["search"])






@router.post("/search_user", response_model=GenericResponseModel, summary="配置群权限")
async def search_user(form: TokenGateItemModel, uid: str = Depends(get_uid_by_token)):
    """
        配置群权限

        有ID就是修改，没有ID就是添加
    """
    items = form.model_dump()
    if form.id:
        del items['id']
        r = await TokenGate.find_one(TokenGate.id==form.id,TokenGate.uid==uid).update({"$set":items})
        return GenericResponseModel()

    else:
        del items['id']
        await TokenGate(**items).create()
        return GenericResponseModel()
@router.post("/search_group", response_model=GenericResponseModel, summary="配置群权限")
async def search_group(form: TokenGateItemModel, uid: str = Depends(get_uid_by_token)):
    """
        配置群权限

        有ID就是修改，没有ID就是添加
    """
    items = form.model_dump()
    if form.id:
        del items['id']
        r = await TokenGate.find_one(TokenGate.id==form.id,TokenGate.uid==uid).update({"$set":items})
        return GenericResponseModel()

    else:
        del items['id']
        await TokenGate(**items).create()
        return GenericResponseModel()
