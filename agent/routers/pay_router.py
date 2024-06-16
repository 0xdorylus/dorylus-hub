from typing import List

from fastapi import APIRouter, Depends, HTTPException

from agent.models.base import GenericResponseModel
from agent.models.pay_product import PayProductItem, PayProduct, PayConfirmItem

from agent.services.acl_service import AclService

from agent.services.pay_service import PayService
from agent.utils.common import filter_empty_value
from agent.utils.x_auth import get_uid_by_token

router = APIRouter(prefix="/pay", tags=["pay"])





@router.get("/get_product_list", response_model=GenericResponseModel[List[PayProductItem]], summary="支付产品列表")
async def get_product_list():
    """
        支付产品列表
    """
    outs: List[PayProductItem] = []
    items = await PayProduct.find_all().to_list()
    for item in items:
        outs.append(PayProductItem(**item.model_dump()))
    return GenericResponseModel(result=outs)

@router.post("/upsert_product", response_model=PayProductItem, summary="添加修改产品")
async def upsert_product( form: PayProductItem, acl_service: AclService = Depends(),uid: str = Depends(get_uid_by_token)):
    """
        添加修改产品
    """
    if acl_service.user_can_create_agent(uid):


        print(form)
        if form.id:
            id = form.id
            product = await PayProduct.get(id)
            if not product:
                raise HTTPException(404, "achieve_not_found")

            data = filter_empty_value(form)
            update_query = {"$set": data}
            item = await PayProduct.find_one(PayProduct.id == form.id).update(update_query)
        else:
            data = form.model_dump()
            del data['id']
            item = await PayProduct(**data).create()
        return item
    else:
        raise HTTPException(403, "Can't Create")


@router.post("/pay_confirm", response_model=GenericResponseModel, summary="支付确认")
async def pay_confirm( form: PayConfirmItem, acl_service: AclService = Depends(),uid: str = Depends(get_uid_by_token)):
    """
        支付确认
    """
    return await  PayService.verify_ios_pay(uid,form.order_id,form.ticket)




