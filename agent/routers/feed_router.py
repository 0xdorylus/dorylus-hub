import math
from typing import List

import pymongo
from fastapi import APIRouter, Depends, Response, HTTPException

from pydantic import BaseModel


from agent.models.base import GenericResponseModel
from agent.models.request_response_model import UserInfoModel, GeneralRequestModel, IDModel

from agent.models.user import User
from agent.models.user_social import UserFollow, UserTweet
from agent.services.feed_service import FeedService

from agent.utils.common import success_return, error_return
from agent.utils.x_auth import get_uid_by_token

router = APIRouter(prefix="/feed", tags=["feed"])


class FollowRequestModel(BaseModel):
    target:str
@router.post("/follow",response_model=GenericResponseModel,summary="跟随某人")
async def follow(form:FollowRequestModel, uid: str = Depends(get_uid_by_token),feed_service:FeedService=Depends()):
    """根据输入的str
    查找uid、userrname或address
    生成关注请求"""
    # FriendRequest 模型

    user = await User.get(form.target)
    if not user:
        user = await User.find_one(User.username == form.target)
        if not user:
            user = await User.find_one(User.address == form.target)
            if not user:
                user = await User.find_one(User.email == form.target)
    if user:
        target  = user.id
        if target == uid:
            return error_return(403,"can't follow self")
        await feed_service.follow(uid,target)
        user.update_avatar()
        out = UserInfoModel(**user.model_dump())
        return success_return(out)
    else:
        return error_return(404,"Not Found")


@router.post("/unfollow",response_model=GenericResponseModel,summary="跟随某人")
async def unfollow(form:FollowRequestModel, uid: str = Depends(get_uid_by_token),feed_service:FeedService=Depends()):
    """根据输入的str
    查找uid、userrname或address
    生成关注请求"""
    user = await User.get(form.target)
    if not user:
        user = await User.find_one(User.username == form.target)
        if not user:
            user = await User.find_one(User.address == form.target)
            if not user:
                user = await User.find_one(User.email == form.target)
    if user:
        if user.owner == uid:
            return error_return(403,"can't unfollow your agent")
        target  = user.id
        await feed_service.unfollow(uid,target)
        return success_return()
    else:
        return error_return(404,"Not Found")



class TweetRequestModel(BaseModel):
    content:str
    images:List[str]=[]
    tags:List[str]=[]

@router.post("/tweet",response_model=GenericResponseModel,summary="发送推文")
async def tweet(form:TweetRequestModel, uid: str = Depends(get_uid_by_token)):
    """发送推文"""
    # FriendRequest 模型
    data = form.model_dump()
    data['uid'] = uid
    await UserTweet.create(**data)
    return success_return()


class TweetCommentRequest(BaseModel):
    tweet_id: str
    content: str




class FollowItemModel(BaseModel):
    user:UserInfoModel={}
    status:str=""
    create_at:int
    id:str

async def callback_follow_list_item(item):

    print(item)
    target = item.target
    user = await User.get_info(target)
    if user:
        return FollowItemModel(user=user,status=item.status,create_at=item.create_at,id=item.id)
    else:
        return None

@router.post("/following_list",response_model=GenericResponseModel,summary="following_list")
async def following_list(request_form:GeneralRequestModel, uid: str = Depends(get_uid_by_token)):
    query = {
        "uid":uid
    }
    options = {
        "page": request_form.page,
        "pagesize": request_form.pagesize,
        "sort": [("_id", pymongo.DESCENDING)],
    }
    return await UserFollow.get_page(query=query, options=options, callback=callback_follow_list_item, is_async_callback=True)


@router.post("/follower_list",response_model=GenericResponseModel,summary="follower_list")
async def follower_list(request_form:GeneralRequestModel, uid: str = Depends(get_uid_by_token),feed_service:FeedService=Depends()):
    query = {
        "target":uid
    }
    options = {
        "page": request_form.page,
        "pagesize": request_form.pagesize,
        "sort": [("_id", pymongo.DESCENDING)],
    }
    return await UserFollow.get_page(query=query, options=options, callback=callback_follow_list_item, is_async_callback=True)


async def callback_follower_list_item(item):

    print(item)
    target = item.uid
    user = await User.get_info(target)

    # return FollowItemModel(**item.model_dump())

    return FollowItemModel(user=user,status=item.status,create_at=item.create_at,id=item.id)

@router.post("/new_follower_list",response_model=GenericResponseModel,summary="new_follower_list")
async def new_follower_list(request_form:GeneralRequestModel, uid: str = Depends(get_uid_by_token),feed_service:FeedService=Depends()):
    query = {
        "target": uid,
        "status":"unread"
    }
    options = {
        "page": request_form.page,
        "pagesize": request_form.pagesize,
        "sort": [("_id", pymongo.DESCENDING)],
    }
    return await UserFollow.get_page(query=query, options=options, callback=callback_follower_list_item, is_async_callback=True)


@router.post("/set_already_read_", response_model=GenericResponseModel, summary="设置已读")
async def set_already_read_(form: IDModel, uid: str = Depends(get_uid_by_token)):

    id = form.id
    await UserFollow.find_one({"_id":id, "target": uid}).update({"$set":{"status":"read"}})
    return  success_return(id)

