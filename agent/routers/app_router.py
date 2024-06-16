import logging
from hashlib import sha256

from agent import config

from pydantic import BaseModel

from agent.config import CONFIG
from agent.models.request_response_model import CreateAgentModel
from agent.models.user import User
from agent.services.agent_service import AgentService
from agent.services.feed_service import FeedService
from agent.services.user_service import UserService
from agent.utils.common import success_return, get_unique_id, get_host, get_current_time, error_return, get_session_id
from agent.utils.redishelper import get_redis
from agent.models.base import GenericResponseModel

from fastapi import APIRouter, HTTPException, Depends
from agent.utils.x_auth import get_uid_by_token

router = APIRouter(prefix="/app", tags=["app"])


class ChatUserRegisterModel(BaseModel):
    app_uid: str
    username: str=""
    timestamp: int
    signature: str


class ChatUserModel(BaseModel):
    id: str
    app_uid: str=""
    username: str=""


@router.post("/register_user", response_model=GenericResponseModel, summary="注册用户")
async def register_user(form: ChatUserRegisterModel, feed_service: UserService = Depends()):
    """
    根据输入生成signature
    sign = sha256(username+uid+timestamp+share_key)
    """

    s = form.username + form.app_uid + str(form.timestamp) + CONFIG.app_key
    sign = sha256(s.encode()).hexdigest()
    print(s)
    print(form)
    print(sign)
    if sign != form.signature:
        return error_return(403, "signature_error",{"sign":sign})
    user = await User.find_one({"username":form.username})
    if user is not None:
        return error_return(401, "exists")
    else:
        data = form.model_dump()
        user = await User(**data).create()

        if CONFIG.system_agent_id:
            await FeedService.follow(user.id, CONFIG.system_agent_id)

        user.update_avatar()
        name = "i-" + user.username
        form = CreateAgentModel(username=name, avatar=user.avatar)
        ret = await AgentService.create_agent(user.id, form)
        if ret.code == 0:
            await FeedService.follow(user.id, ret.result['user'].id)


        print(user)
        data = ChatUserModel(**user.model_dump())
        return success_return(data)


@router.post("/login_user", response_model=GenericResponseModel, summary="登录用户")
async def login_user(form: ChatUserRegisterModel, user_service: UserService = Depends()):
    """
    根据输入生成signature
    sign = sha256(username+uid+timestamp+share_key)
    """

    s = form.username + form.app_uid + str(form.timestamp) + CONFIG.app_key
    sign = sha256(s.encode()).hexdigest()
    print(form)
    print(sign)
    if sign != form.signature:
        return error_return(403, "signature_error",{"sign":sign})
    user = await User.find_one({"app_uid":form.app_uid})
    if user is not None:
        redis = await get_redis()
        sid = get_session_id()
        await redis.set(sid, user.id)
        await redis.set("app"+form.app_uid,sid)
        return success_return({"sid":sid,"uid":form.app_uid,"id":user.id})
    else:
        return error_return(401, "not_exists")

@router.post("/logout_user", response_model=GenericResponseModel, summary="退出IM登录")
async def logout_user(form: ChatUserRegisterModel, user_service: UserService = Depends()):
    """
    根据输入生成signature
    sign = sha256(username+uid+timestamp+share_key)
    """

    s = form.username + form.app_uid + str(form.timestamp) + CONFIG.app_key
    sign = sha256(s.encode()).hexdigest()
    print(form)
    print(sign)
    if sign != form.signature:
        return error_return(403, "signature_error",{"sign":sign})
    user = await User.find_one({"app_uid":form.app_uid})
    if user is not None:
        k = "app"+form.app_uid
        redis = await get_redis()
        sid = await redis.get(k)
        if sid is not None:
            await redis.delete(k)
            await redis.delete(sid)
        return success_return()
    else:
        return error_return(401, "not_exists")


@router.post("/send", response_model=GenericResponseModel, summary="给一个用户发送消息")
async def send(form: ChatUserRegisterModel, user_service: UserService = Depends()):
    """
    根据输入生成signature
    sign = sha256(username+uid+timestamp+share_key)
    """

    s = form.username + form.app_uid + str(form.timestamp) + CONFIG.app_key
    sign = sha256(s.encode()).hexdigest()
    print(form)
    print(sign)
    if sign != form.signature:
        return error_return(403, "signature_error",{"sign":sign})
    user = await User.find_one({"uid":form.app_uid})
    if user is not None:
        k = "app"+form.app_uid
        redis = await get_redis()
        sid = await redis.get(k)
        if sid is not None:
            await redis.delete(k)
            await redis.delete(sid)
        return success_return()
    else:
        return error_return(401, "not_exists")
