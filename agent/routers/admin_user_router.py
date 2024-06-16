import math
from datetime import datetime
from typing import List

from pydantic import BaseModel

from agent.models.biz_user import BizLoginModel, BizUserModel
from agent.models.request_response_model import BizAuthResponseModel, \
    PageRequestModel, UserInfoModel, DeviceIdLoginModel
from agent.models.system_prompt import SystemtPromptForm, SystemPrompt
from agent.models.system_tag import SystemTag, SystemtTagForm
from agent.services.acl_service import AclService
from agent.utils.blockhelper import verify_signature
from agent.utils.common import success_return, encode_input, error_return, get_unique_id
from agent.utils.redishelper import get_redis
from agent.models.base import GenericResponseModel
from agent.models.user import LoginWithSignModel, User, LoginWithUsernameModel, LoginWithUsername, SignUpWithEmailModel, \
    VerifyEmailModel
from fastapi import APIRouter, HTTPException, Depends

from agent.utils.x_auth import get_uid_by_token, get_biz_uid_by_token

from agent.services.user_service import UserService
from fastapi import Depends,Request
from fastapi.encoders import jsonable_encoder
from fastapi import FastAPI, Query
router = APIRouter(prefix="/admin", tags=["admin"])



class UserListRequestModel(BaseModel):
    page: int = 1
    pagesize: int = 10


class UserListItemModel(BaseModel):
    id: str
    title: str
    content: str = ""
    creator: UserInfoModel = {}
    create_at: datetime = datetime.now()


class UserListResponseModel(BaseModel):
    total: int = 0
    total_page: int = 1
    list: List[UserListItemModel] = []


@router.post("/account/users", GenericResponseModel[UserListResponseModel],response_description="会员列表")
async def user_list(request_form: UserListRequestModel,uid: str = Depends(get_uid_by_token)):
    users = await User.find_all().to_list()

    skip = (request_form.page - 1) * request_form.pagesize

    limit = request_form.pagesize
    items: List[UserListItemModel] = []

    sort = (-User.id)
    query = {}

    # print(query)
    total = await User.find(query).count()
    total_page = math.ceil(total / request_form.pagesize)
    objects = await User.find(query).sort(sort).skip(skip).limit(limit).to_list()
    for item in objects:
        vo = UserListItemModel(**item.dict())
        vo.creator = await User.get_info(item.uid)
        items.append(vo)

    response_model = UserListResponseModel()
    response_model.total = total
    response_model.list = items
    response_model.total_page = total_page
    return GenericResponseModel(result=response_model)

    return success_return(users)


class UserAddFormModel(BaseModel):
    pid:str
@router.post("/account/add_user", GenericResponseModel,response_description="添加用户")
async def add_user(request_form: UserAddFormModel,uid: str = Depends(get_biz_uid_by_token)):
    pid = request_form.pid
    user  = await User.get(pid)
    if not user:
        return error_return(404,"not_found_user")
    else:
        data = {
            "device_id":get_unique_id(),
            "refcode":user.invite_code
        }
        dto = DeviceIdLoginModel(**data)
        user = await UserService.create_user_with_device_id(dto)
        return success_return(user)


# @router.post("/business/login", response_model=GenericResponseModel[BizAuthResponseModel], response_description="登录后台")
# async def biz_login(login_form: BizLoginModel,  request: Request,user_service: UserService = Depends()):
#     print(login_form)
#     data= await user_service.biz_user_login(login_form)
#     return GenericResponseModel(result=data)
#
# @router.post("/business/create", response_model=GenericResponseModel[BizAuthResponseModel], response_description="登录后台")
# async def biz_user_create(form: BizUserModel,  request: Request,user_service: UserService = Depends()):
#     data= await user_service.create_biz_user(form)
#     return GenericResponseModel(result=data)
#
# @router.post("/tags/create", tags=["admin"],response_model=GenericResponseModel[SystemTag],response_description="Review records retrieved")
# async def create(tag_form:SystemtTagForm ,uid: str = Depends(get_uid_by_token))->GenericResponseModel:
#     data = encode_input(tag_form)
#     filter = {
#         "tag":tag_form.tag,
#         "title":tag_form.title
#     }
#     doc = await SystemTag.find_one(filter)
#     if doc:
#         return GenericResponseModel(code=1,message="Already exists")
#
#     else:
#         doc  = await SystemTag(**data).create()
#         return GenericResponseModel(result=doc)
#
#
#
# @router.post("/tags/list", tags=["admin"],response_model=GenericResponseModel[List[SystemTag]],response_description="Review records retrieved")
# async def list_tags(form:PageRequestModel,uid: str = Depends(get_uid_by_token))->GenericResponseModel:
#
#
#     data = await SystemTag.find_all().to_list()
#
#     return GenericResponseModel(result=data)
#
# @router.post("/tags/view", response_model=GenericResponseModel[SystemTag],tags=["admin"])
# async def view_tag(id:str,uid: str = Depends(get_uid_by_token))->GenericResponseModel:
#     data = await SystemTag.find_one(SystemTag.id == id)
#     return GenericResponseModel(result=data)
#
#
# @router.post("/prompt/create", tags=["admin"],response_model=GenericResponseModel[SystemPrompt],response_description="Review records retrieved")
# async def create_prompt(form:SystemtPromptForm ,uid: str = Depends(get_uid_by_token))->GenericResponseModel:
#     data = encode_input(form)
#     filter = {
#         "name":form.name
#     }
#     doc = await SystemPrompt.find_one(filter)
#     if doc:
#         return GenericResponseModel(code=1,message="Already exists")
#     else:
#         doc  = await SystemPrompt(**data).create()
#         return GenericResponseModel(result=doc)
#
#
# @router.post("/prompt/list", tags=["admin"],response_model=GenericResponseModel[List[SystemPrompt]],response_description="Review records retrieved")
# async def list_prompt(form:PageRequestModel,uid: str = Depends(get_uid_by_token)):
#
#
#     data = await SystemPrompt.find_all().to_list()
#
#     return GenericResponseModel(result=data)
#
#
# @router.post("/prompt/view",response_model=GenericResponseModel[SystemPrompt] ,tags=["admin"])
# async def view_prompt(id:str,uid: str = Depends(get_uid_by_token))->GenericResponseModel:
#     data = await SystemPrompt.get(id)
#     return GenericResponseModel(result=data)