import logging
from typing import List

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel

from agent.models.assistant import AssistantDetailModel, GirlDetailModel
from agent.models.base import GenericResponseModel
from agent.models.channel import ChanndelItemModel
from agent.models.request_response_model import UserDetailModel, FinishResponseModel, CaptchaMode, IDModel, HotModel

from agent.models.subscribe import Subscription, SubscribeAssistantModel
from agent.models.user import User, UpdateUserModel, UserInfoModel
from agent.models.user_acheievements import UserAchievementStatModel, UserAchievement
from agent.models.user_config import UserConfig
from agent.models.user_social import UserSocial, UserSocialItem
from agent.services.social_service import SocialService
from agent.services.user_service import UserService
from agent.utils.common import success_return,succ,error_return
from pydantic import BaseModel, constr, Field
import os
import random
from agent.utils.x_auth import get_uid_by_token

router = APIRouter(prefix="/user", tags=["User"])
from agent.config import CONFIG

@router.get("/username_available",response_model=GenericResponseModel[bool],summary="用户名可用吗,用户名注册用")
async def username_available(username:str):
    """
        用户名可用吗
    """
    user = await User.find_one(User.username==username)
    if user:
        return GenericResponseModel(result=False)
    else:
        return GenericResponseModel(result=True)

def random_png(directory):
    png_files = [file for file in os.listdir(directory) if file.endswith(".png")]
    if png_files:
        random_file = random.choice(png_files)
        return  random_file
    else:
        return None

@router.get("/get_random_avatar",response_model=GenericResponseModel[str],summary="获取随机头像")
async def get_random_avatar():
    """

    """
    src_dir = "/deploy/dorylus/s/avatar"
    file = random_png(src_dir)
    url = CONFIG.file_domain + "/avatar/" + file

    return GenericResponseModel(result=url)


class UserPropertyValueModel(BaseModel):
    value: str = Field("", min_length=1, max_length=132)
    key: str = Field("", min_length=1, max_length=32)

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "value": "John",
                "key": "nickname"
            }
   }


@router.post("/set_nickname",response_model=GenericResponseModel,summary="设置昵称？")
async def set_nickname(form:UserPropertyValueModel,uid: str = Depends(get_uid_by_token)):
    """
    """
    return await User.set_property(uid,"nickname",form.value)

@router.post("/detail",response_model=GenericResponseModel,summary="设置昵称？")
async def user_detail(id:str,uid: str = Depends(get_uid_by_token)):
    """
    """
    user = await User.get(id)
    data = UserDetailModel(**user.model_dump())
    return GenericResponseModel(result=data)


@router.post("/set_avatar",response_model=GenericResponseModel,summary="设置头像？")
async def set_avatar(form:UserPropertyValueModel,uid: str = Depends(get_uid_by_token)):
    """
    """
    return await User.set_property(uid,"avatar",form.value)


@router.post("/set_hot_model",response_model=GenericResponseModel,summary="切换HOT模式")
async def set_hot_model(form:HotModel, uid: str = Depends(get_uid_by_token)):
    """
    hot值为空或"hot"字符串

    """
    ret = await UserConfig.set_hot_model(uid,form.hot)
    return GenericResponseModel()
@router.get("/me",response_model=GenericResponseModel[UserDetailModel],summary="获取个人基本数据")
async def get_self( user_service: UserService = Depends(),uid: str = Depends(get_uid_by_token)):
    """
        获取用户当前资料
    """
    data = await user_service.get_user(uid)

    return GenericResponseModel(result= data)

@router.get("/achievements",response_model=GenericResponseModel[UserAchievementStatModel],summary="获取个人成就")
async def get_user_achieve_stat( uid: str = Depends(get_uid_by_token)):
    """
        获取用户当前成就
    """
    data = await UserAchievement.get_stat_list(uid)

    return GenericResponseModel(result= data)

@router.get("/social_list",response_model=GenericResponseModel[List[UserSocialItem]],summary="获取个人社交链接")
async def get_user_social_list( uid: str = Depends(get_uid_by_token)):
    """
        获取用户当前社交链接
    """
    data = await UserSocial.get_social_list(uid)

    return GenericResponseModel(result= data)
@router.post("/kill_self",response_model=GenericResponseModel,summary="删除自己的资料，让账号无效")
async def kill_self(form:CaptchaMode, user_service: UserService = Depends(),uid: str = Depends(get_uid_by_token))->UserInfoModel:
    """
        用户删除自己的资料

        让账号无效
    """
    logging.info(form.code)
    await User.kill_self(uid)

    return GenericResponseModel()



class ReferalModel(BaseModel):
    code:str

@router.post("/set_parent",response_model=GenericResponseModel[UserDetailModel],summary="更新资料，为空忽略")
async def set_parent(form:ReferalModel, uid: str = Depends(get_uid_by_token)):
    code = form.code
    user = await User.find_one(User.id == uid)
    parent_user = await User.find_one(User.invite_code == code)
    if not parent_user:
        parent_user = await User.find_one(User.username == code)
        if not parent_user:
            parent_user = await User.find_one(User.address == code)
    if not parent_user:
        return error_return(1,"invite_code_error",user)

    if user.id == parent_user.id:
        return error_return(2,"invite_self_error",user)

    parents_id = await User.get_parents_ids(uid)
    if parent_user.id in parents_id:
        return error_return(3,"invite_cycle_error",user)
    await User.set_parent(uid,parent_user.id)
    return success_return(user)




@router.post("/update_profile",response_model=GenericResponseModel[UserDetailModel],summary="更新资料，为空忽略")
async def update_profile(form:UpdateUserModel, uid: str = Depends(get_uid_by_token)):
    """
        更新用户资料，为空的忽略
    :param update_user:
    :param uid:
    :return:
    """
    logging.info(form)
    print('form_pid',form.pid)
    userinfo = await User.get(uid)
    ppid = 0
    if form.pid != 0:
        pid = await User.find_one(User.invite_code == form.pid)
        if pid:
            form.pid = pid.id
            ppid = 1
        else:
            newuser = await User.find_one(User.username == form.pid)
            if newuser:
                form.pid = newuser.id
                ppid = 1
    print('ppid',ppid,form.pid,userinfo.invite_code,userinfo.username)

    if userinfo.id == form.pid:
        print('22',form.pid,ppid)
        return error_return(0,"not bding user",userinfo)

    if form.pid and ppid == 0:
        print('33',form.pid,ppid)
        return error_return(0, "not bding code", userinfo)


    ret = await User.update_profile(uid,form)
    return GenericResponseModel(result=ret)



@router.post("/subscribe_assistant",response_model=GenericResponseModel[ChanndelItemModel],summary="订阅AI角色")
async def subscribe_assistant(form:SubscribeAssistantModel, social_service:SocialService=Depends(),uid: str = Depends(get_uid_by_token)):
    """
        没有订阅就自动改订阅，订阅后返回订阅的频道
    """
    channel = await social_service.subscribe_agent(uid, form.assistant_id)

    data =  ChanndelItemModel(**channel.model_dump())
    return GenericResponseModel(result=data)

@router.post("/unsubscribe_assistant",response_model=GenericResponseModel,summary="取消订阅AI角色")
async def unsubscribe_assistant(form:IDModel, social_service:SocialService=Depends(),uid: str = Depends(get_uid_by_token)):
    """
        取消订阅
    """
    assistant_id = form.id
    await social_service.unsubscribe_assistant(uid,assistant_id)
    return GenericResponseModel()

@router.post("/delegate",response_model=GenericResponseModel,summary="将对话委托给我创建的AI角色(dev)")
async def delegate_assistant(form:IDModel, uid: str = Depends(get_uid_by_token)):
    """
    让AI角色替我聊天

    开发中

    """
    assistant_id = form.id
    ret = await User.delegate_assistant(uid,assistant_id)
    return GenericResponseModel()

@router.get("/my_subscribed_assistant_list",response_model=GenericResponseModel[List[AssistantDetailModel]],summary="我订阅的AI列表")
async def my_subscribed_assistant_list(user_service: UserService = Depends(),uid: str = Depends(get_uid_by_token)):
    data =await user_service.user_subscribed_assistant_list(uid)
    return GenericResponseModel(result=data)


@router.get("/my_subscribed_girls_list",response_model=GenericResponseModel[List[GirlDetailModel]],summary="我订阅的AI列表")
async def my_subscribed_girls_list(user_service: UserService = Depends(),uid: str = Depends(get_uid_by_token)):
    data =await user_service.my_subscribed_girls_list(uid)
    return GenericResponseModel(result=data)

@router.post("/get_pid",response_model=GenericResponseModel[str],summary="获取父节点")
async def get_pid(uid: str = Depends(get_uid_by_token)):
    user =  await User.get(uid)
    if user:
        pid = user.pid
        return GenericResponseModel(code=0,message="",result=pid)
    else:
        return GenericResponseModel(code=1,message="system_error")
#
# @router.post("/add_social_link",response_model=GenericResponseModel,summary="增加社交链接")
# async def add_soci(user_service: UserService = Depends(),uid: str = Depends(get_uid_by_token)):
#     await user_service.user_subscribed_assistant_list(uid)
#     return GenericResponseModel()

class LangSetModel(BaseModel):
    lang:str
@router.post("/set_default_lang",response_model=GenericResponseModel[str],summary="获取父节点")
async def set_default_lang(form:LangSetModel,uid: str = Depends(get_uid_by_token)):
    await User.set_lang(uid,form.lang)
    return GenericResponseModel(result=form.lang)
