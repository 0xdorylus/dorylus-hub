from typing import List

from fastapi import APIRouter, Depends, Response, HTTPException

from agent.models.base import GenericResponseModel
from agent.models.request_response_model import FinishResponseModel, IDModel
from agent.models.token_gate import TokenGateItemModel, TokenGate
from agent.utils.x_auth import get_uid_by_token

router = APIRouter(prefix="/wers", tags=["wers"])






@router.post("/upsert_group_acl_item", response_model=GenericResponseModel, summary="配置群权限")
async def upsert_group_acl_item(form: TokenGateItemModel, uid: str = Depends(get_uid_by_token)):
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


@router.post("/del_group_acl_item", response_model=GenericResponseModel, summary="删除一条权限")
async def del_group_acl_item(form:IDModel, uid: str = Depends(get_uid_by_token)):
    """
        删除一条权限
    """

    r = await TokenGate.find_one(TokenGate.id==form.id,TokenGate.uid==uid).delete_one()
    if r.deleted_count==1:
        return GenericResponseModel()
    else:
        return GenericResponseModel(code=301,message="not_modified")

@router.post("/list_group_acl_item", response_model=GenericResponseModel[List[TokenGateItemModel]], summary="群权限列表")
async def list_group_acl_item(form:IDModel):
    """
        群权限列表
    """
    data =  await TokenGate.get_acl_items(form.id)
    return GenericResponseModel(result=data)



