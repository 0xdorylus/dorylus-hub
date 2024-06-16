import math
from typing import List

from fastapi import APIRouter, Depends, Response

from agent.models.base import GenericResponseModel
from agent.models.subscribe import Subscription
from agent.models.tool import Tool, ToolModel
from agent.models.user import User
from agent.utils.common import success_return
from agent.utils.x_auth import get_uid_by_token
from fastapi import Query

router = APIRouter(prefix="/tool", tags=["tool"])




@router.post("/list",response_model=GenericResponseModel)
async def list_tool(page: int = Query(1, ge=1), uid: str = Depends(get_uid_by_token)):
    per_page = 10
    skip = (page - 1) * per_page
    limit = 10


    sort = (-Tool.id)
    # sort = ()
    filter = {}


    total = await Tool.find(filter).count()
    total_page = math.ceil(total / per_page)
    objects = await Tool.find(filter).sort(sort).skip(skip).limit(limit).to_list()
    out_list = []

    for item in objects:
        object = ToolModel(**item.dict())
        out_list.append(object)
    #
    # data = ('total': total,
    #     'list': out_list,
    #     'total_page': total_page
    # )

    return GenericResponseModel()


# @router.post("/create")
# async def create_tool(mainchain:str="BSC", uid: str = Depends(get_uid_by_token)):
#     """Get current user"""
#     return {"uid": uid}
