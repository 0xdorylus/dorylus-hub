
from typing import List


from agent.models.biz_user import BizLoginModel, BizUserModel
from agent.models.request_response_model import BizAuthResponseModel, \
    PageRequestModel
from agent.models.system_prompt import SystemtPromptForm, SystemPrompt
from agent.models.system_tag import SystemTag, SystemtTagForm
from agent.services.acl_service import AclService
from agent.utils.blockhelper import verify_signature
from agent.utils.common import success_return, encode_input, error_return
from agent.utils.redishelper import get_redis
from agent.models.base import GenericResponseModel
from agent.models.user import LoginWithSignModel, User, LoginWithUsernameModel, LoginWithUsername, SignUpWithEmailModel, \
    VerifyEmailModel
from fastapi import APIRouter, HTTPException, Depends

from agent.utils.x_auth import get_uid_by_token

from agent.services.user_service import UserService
from fastapi import Depends,Request
from fastapi.encoders import jsonable_encoder
from fastapi import FastAPI, Query
router = APIRouter(prefix="/admin", tags=["admin"])





@router.post("/biz_login", response_model=GenericResponseModel[BizAuthResponseModel], response_description="登录后台")
async def biz_login(login_form: BizLoginModel,  request: Request,user_service: UserService = Depends()):
    print(login_form)
    data= await user_service.biz_user_login(login_form)
    return GenericResponseModel(result=data)

@router.post("/business/create", response_model=GenericResponseModel[BizAuthResponseModel], response_description="登录后台")
async def biz_user_create(form: BizUserModel,  request: Request,user_service: UserService = Depends()):
    data= await user_service.create_biz_user(form)
    return GenericResponseModel(result=data)
