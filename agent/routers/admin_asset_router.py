import logging
import math
from typing import List

from pydantic import BaseModel


from agent.models.user_asset import UserAsset

from agent.utils.common import success_return, encode_input, error_return
from agent.models.base import GenericResponseModel

from fastapi import APIRouter, HTTPException, Depends

from agent.utils.x_auth import get_uid_by_token, get_biz_uid_by_token

from agent.services.user_service import UserService
from fastapi import Depends,Request
from fastapi.encoders import jsonable_encoder
from fastapi import FastAPI, Query
router = APIRouter(prefix="/admin/asset", tags=["admin_asset"])



class SimulateAssetModel(BaseModel):
    uid:str
    token:str
    amount:float
    mainchain:str="BSC"
@router.post("/simulate_add", response_description="simulate add asset")
async def simulate_add_asset(form:SimulateAssetModel,uid: str = Depends(get_biz_uid_by_token),user_service: UserService = Depends())->GenericResponseModel:
    # flag = await UserAsset.incr(form.uid,form.mainchain,form.token,form.amount,"simulate_add_asset","simulate add asset")
    # if flag:
    #     return success_return()
    # else:
    #     return error_return("simulate add asset error")
    pass





