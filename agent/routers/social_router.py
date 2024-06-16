import math
from typing import List, Optional

from fastapi import APIRouter, Depends, Response, HTTPException
from datetime import datetime

from agent.config import CONFIG
from agent.errors.biz import UserNotInChannel
from agent.models.acl import Acl
from agent.models.base import GenericResponseModel
from agent.models.channel import Channel, ChanndelItemModel
from agent.models.chat_message import ChatMessage, ChatDialogMessageModel, SendMessageModel, ChatGroupMessage, \
    ChatDialogMessage, ChatGroupMessageModel, ChatGroupUserMessagePosition
from agent.models.contact import Contact
from agent.models.conversation import Conversation, ConversationListItem
from agent.models.friend_request import FriendRequest, AddFriendRequestModel, FriendRequestItemModel, \
    FriendRequestListModel, DealFriendRequestModel, JoinGroupRequest, JoinGroupRequestItem
from agent.models.request_response_model import CreateGroupModel, GroupDetailModel, UpdateGroupModel, \
    ChannelUserListResponseModel, UserInfoModel, FinishResponseModel, GroupListRequestModel, GroupListResponseModel, \
    IDModel, JoinGroupRequestModel, PageRequestModel, HistoryPageRequestModel, SearchModel, GroupInfoModel, \
    MessageModel, UserDetailModel
from agent.models.subscribe import Subscription
from agent.models.token_gate import TokenGate, TokenGateItemModel
from agent.models.user import User
from agent.models.user_channel import UserChannel
from agent.models.user_social import UserFollow
from agent.services.assistant_service import AssistantService
from agent.services.social_service import SocialService
from agent.utils.common import success_return, error_return, get_current_time
from agent.utils.x_auth import get_uid_by_token
from fastapi import Query

router = APIRouter(prefix="/social", tags=["social"])


@router.post("/join_channel", response_model=GenericResponseModel, summary="用户进入一个频道")
async def join_channel(form: IDModel, uid: str = Depends(get_uid_by_token)):
    """
    可以是点对点
    也可以是群
    """
    channel_id = form.id
    channel = await Channel.find_one({"_id": channel_id, "user_ids": {"$in": [uid]}})
    if not channel:
        raise UserNotInChannel("user_not_in_channel")
    is_first_join = await UserChannel.is_first_join(uid, channel_id)
    if is_first_join:
        await UserChannel.create(uid=uid, channel_id=channel_id, join_at=get_current_time())
        if channel_id == CONFIG.system_agent_id:  # 默认的系统频道
            pass

    return GenericResponseModel()

from pydantic import BaseModel
class DeleteUserFromChannelModel(BaseModel):
    channel_id:str
    uid:str
@router.post("/delete_user_from_channel", response_model=GenericResponseModel, summary="从频道删除用户")
async def delete_user_from_channel(form: DeleteUserFromChannelModel, uid: str = Depends(get_uid_by_token)):

    channel_id = form.channel_id

    channel = await Channel.find_one({"_id": channel_id, "admin_ids": {"$in": [uid]}})
    if channel is None:
        return error_return(403,"Forbidden")

    channel.admin_ids.remove(form.uid)
    await channel.save()
    return success_return()

@router.post("/add_friend_request", response_model=GenericResponseModel, summary="添加好友请求")
async def add_friend_request(form: AddFriendRequestModel, uid: str = Depends(get_uid_by_token)):
    """根据输入的str
    查找uid、userrname或address
    生成添加好友请求"""
    # FriendRequest 模型
    data = form.model_dump()

    found = False
    if await User.get(form.target):
        found = True
    elif await User.find_one(User.username == form.target):
        found = True
    elif await User.find_one(User.adddress == form.target):
        found = True
    if found:
        data['sender'] = uid
        data['receiver'] = form.target
        await FriendRequest(**data).create()

        return GenericResponseModel()
    else:
        raise HTTPException(404, "Not Found")


@router.post("/friend_request_list", response_model=GenericResponseModel[FriendRequestListModel],
             summary="别人请求我和我请求别人的列表")
async def friend_request_list(form: PageRequestModel, uid: str = Depends(get_uid_by_token)):
    """别人请求我和我请求别人的"""
    recieve_list: List[FriendRequestItemModel] = []
    send_list: List[FriendRequestItemModel] = []
    filter = {}
    filter['sender'] = uid
    items = await FriendRequest.find(filter).to_list()
    for item in items:
        o = FriendRequestItemModel(**item.model_dump())
        send_list.append(o)

    filter['receiver'] = uid
    items = await FriendRequest.find(filter).to_list()
    for item in items:
        o = FriendRequestItemModel(**item.model_dump())
        recieve_list.append(o)

    response_model = FriendRequestListModel()
    response_model.recieve_list = recieve_list
    response_model.send_list = send_list
    return GenericResponseModel(result=response_model)


@router.post("/accept_friend_request", response_model=GenericResponseModel, summary="接受好友请求")
async def accept_friend_request(form: DealFriendRequestModel, uid: str = Depends(get_uid_by_token)):
    """接受好友请求"""
    vo = await  FriendRequest.get(form.id)
    if vo:
        if vo.receiver == uid:
            channel = await Channel.create_friend_channel(vo.sender, vo.receiver)
            await Conversation.add_friend_conversation(uid, vo.sender, channel.id)
            await Conversation.add_friend_conversation(vo.sender, uid, channel.id)
            await FriendRequest.accept(form.id)

            return GenericResponseModel()
        else:
            raise HTTPException(403, "Forbidden")
    else:
        raise HTTPException(404, "Forbidden")


@router.post("/deny_friend_request", response_model=GenericResponseModel, summary="拒绝好友请求")
async def deny_friend_request(form: DealFriendRequestModel, uid: str = Depends(get_uid_by_token)):
    """
    拒绝
    :param form:
s    :return:
    """
    vo = await  FriendRequest.get(form.id)
    if vo:
        if vo.receiver == uid:
            await FriendRequest.deny(form.id)
            return GenericResponseModel()
        else:
            raise HTTPException(403, "Forbidden")
    else:
        raise HTTPException(404, "Not Found")


@router.post("/create_group", response_model=GenericResponseModel, summary="创建群")
async def create_group(form: CreateGroupModel, uid: str = Depends(get_uid_by_token),
                       social_service: SocialService = Depends()):
    """
    创建群

    """
    return await SocialService.create_group(uid, form)


@router.post("/groups", response_model=GenericResponseModel[GroupListResponseModel], summary="群列表")
async def list_group(request_form: GroupListRequestModel):
    """
    群列表
    """

    skip = (request_form.page - 1) * request_form.pagesize

    limit = request_form.pagesize
    items: List[GroupDetailModel] = []

    sort = (-Channel.id)
    filter = {
        "type": "group"
    }

    total = await Channel.find(filter).count()

    total_page = math.ceil(total / request_form.pagesize)

    objects = await Channel.find(filter).sort(sort).skip(skip).limit(limit).to_list()
    for item in objects:
        object = GroupDetailModel(**item.dict())
        object.creator = await User.get_info(item.uid)
        items.append(object)

    data = GroupListResponseModel(total=total, total_page=total_page, list=items)
    return GenericResponseModel(result=data)


@router.post("/update_group", response_model=GenericResponseModel[GroupDetailModel], summary="更新群")
async def update_group(form: UpdateGroupModel, uid: str = Depends(get_uid_by_token),
                       social_service: SocialService = Depends()):
    """
    修改群
    """
    data = await social_service.update_group(uid, form)
    return GenericResponseModel(result=data)


@router.post("/try_join_group", response_model=GenericResponseModel, summary="尝试加入群聊")
async def try_join_group(form: IDModel, uid: str = Depends(get_uid_by_token)):
    """
        加入群聊申请，如果不需要授权，则直接通过，返回[]

        如果需要授权，则返回需要的检查的，做额外处理

    """
    channel = await Channel.get(form.id)
    if channel is not None:
        await channel.user_join_channle(uid)
        await Conversation.add_group_conversation(uid, channel.id, channel.name)

        return success_return({"id":channel.id})
        # who_can_join = channel.who_can_join
        # if who_can_join == "anyone":
        #     await channel.user_join_channle(uid)
        #     return success_return()
        # else:
        #     items = await TokenGate.get_acl_items(form.id)
        #
        #     return GenericResponseModel(result=items)
        # if channel.is_public:
        #     await channel.user_join_channle(uid)
        #     return []
        # else:
        #     items = await TokenGate.get_acl_items(form.id)
        #
        #     return GenericResponseModel(result=items)
    else:
        raise HTTPException(404, "group_not_found")



from pydantic import BaseModel
class InviteModel(BaseModel):
    user_ids:List[str]
    channel_id:str


@router.post("/invite_to_group", response_model=GenericResponseModel, summary="加入群聊")
async def invite_to_group(form: InviteModel, uid: str = Depends(get_uid_by_token)):
    """
        邀请用户加入群聊
    """
    channel = await Channel.get(form.channel_id)
    succ_list=[]
    if channel is not None:
        user_ids = list(set(form.user_ids))
        for tuid in user_ids:
            user = await User.get(tuid)
            print(tuid)
            print(user)
            if user is not None:

                # if user.accept_invite_join_group:
                await channel.user_join_channle(tuid)
                await Conversation.add_group_conversation(tuid, channel.id, channel.name)
                succ_list.append(tuid)

        return success_return({"users":succ_list})

    else:
        raise HTTPException(404, "group_not_found")



@router.post("/quit_group", response_model=GenericResponseModel, summary="退出群聊")
async def quit_group(form: IDModel, uid: str = Depends(get_uid_by_token)):
    channel = await Channel.get(form.id)
    if channel is not None:
        if uid in channel.user_ids:
            channel.user_ids.remove(uid)
        if uid in channel.admin_ids:
            channel.admin_ids.remove(uid)
        await channel.save()
        await Conversation.drop_group_conversation(uid, form.id)
        return GenericResponseModel()
    else:
        return error_return(404, "group_not_found")


@router.post("/join_group_request", response_model=GenericResponseModel, summary="加入群聊")
async def join_group_request(form: JoinGroupRequestModel, uid: str = Depends(get_uid_by_token)):
    """
        加入群聊申请，token和nft都不满足条件下，群主手动同意

        id是channel_id(group_id)
    """
    channel = await Channel.get(form.id)
    if channel:
        data = {
            "channel_id": form.id,
            "uid": uid,
            "memo": form.memo,
            "admin_uids": channel.admin_ids
        }
        await JoinGroupRequest(**data).create()
        return GenericResponseModel()

    else:
        raise HTTPException(404, "group_not_found")


@router.post("/list_join_group_request", response_model=GenericResponseModel[List[JoinGroupRequestItem]],
             summary="加入群聊")
async def list_join_group_request(uid: str = Depends(get_uid_by_token)):
    """
        加入群聊申请，token和nft都不满足条件下，群主手动同意

        id是channel_id(group_id)
    """
    filter = {
        "admin_uids": {"$in": [uid]},
        "status": "pending"
    }
    outs: List[JoinGroupRequestItem] = []
    items = await JoinGroupRequest.find(filter).to_list()
    for item in items:
        outs.append(JoinGroupRequestItem(**item.model_dump()))
    return GenericResponseModel(result=outs)


@router.post("/accept_join_group_request", response_model=GenericResponseModel, summary="同意加入群申请")
async def accept_join_group_request(form: IDModel, uid: str = Depends(get_uid_by_token)):
    item = await JoinGroupRequest.get(form.id)
    if item:
        channel_id = item.channel_id
        channel = await Channel.get(channel_id)
        if channel:
            await channel.user_join_channle(item.uid)
            await JoinGroupRequest.accept(uid, form.id)
            return GenericResponseModel()
        else:
            raise HTTPException(404, "group_not_found")
    else:
        raise HTTPException(404, "join_group_request_not_found")


@router.post("/deny_join_group_request", response_model=GenericResponseModel, summary="拒绝加入群申请")
async def deny_join_group_request(form: IDModel, uid: str = Depends(get_uid_by_token)):
    item = await JoinGroupRequest.get(form.id)
    if item:
        await JoinGroupRequest.deny(uid, form.id)
        return GenericResponseModel()
    else:
        raise HTTPException(404, "join_group_request_not_found")


@router.post("/group_users", response_model=GenericResponseModel[List[UserInfoModel]], summary="群用户")
async def channel_users(form: IDModel,
                        uid: str = Depends(get_uid_by_token)) -> GenericResponseModel:
    """
        群或频道的用户列表
        ID是群

        TODO：限度特定人查看群成员
    """
    target = form.id
    print(target)
    channel = await Channel.get(target)
    if channel:
        user_ids = channel.user_ids
        user_items: List[UserInfoModel] = []

        for id in user_ids:
            user = await User.get_info(id)
            user_items.append(user)
        return GenericResponseModel(result=user_items)
    else:
        raise HTTPException(404, "Not Found")


@router.post("/get_group_join_link", response_model=GenericResponseModel[str], summary="获得群邀请链接")
async def groups(form: IDModel,
                 uid: str = Depends(get_uid_by_token)):
    """
        邀请其他人加入群

    """
    target = form.id
    channel = await Channel.get(target)
    if channel:
        link = CONFIG.invite_join_group_link + "?id=" + target + "&from_user_id=" + uid
        return GenericResponseModel(result=link)
    else:
        raise HTTPException(404, "Not Found")


@router.post("/chats", response_model=GenericResponseModel[List[ConversationListItem]], summary="会话列表")
async def chats(uid: str = Depends(get_uid_by_token)):
    """会话列表"""
    data = await Conversation.get_chats(uid)
    return GenericResponseModel(result=data)


@router.post("/send", response_model=GenericResponseModel, summary="发送消息")
async def send(items: MessageModel, uid: str = Depends(get_uid_by_token)):
    """


    """
    source = "http"
    return await SocialService.send(uid, items, source)


@router.post("/clear_group_history", response_model=GenericResponseModel, summary="清除群聊历史消息")
async def clear_group_history(form: IDModel, uid: str = Depends(get_uid_by_token)):
    """

    群聊的对话记录

    """
    channel = await Channel.get(form.id)
    if channel is not None and channel.type == "group":
        objects = await ChatGroupMessage.find({"channel_id": form.id}).sort(-ChatGroupMessage.id).first_or_none()
        if objects is not None:
            last_message_id = objects.id
            await ChatGroupUserMessagePosition.update_last_message_id(form.id, uid, last_message_id)
        return GenericResponseModel()
    else:
        return GenericResponseModel(code=1, message="error_parameter")


@router.post("/clear_dialog_history", response_model=GenericResponseModel, summary="清除对话历史消息")
async def clear_dialog_history(form: IDModel, uid: str = Depends(get_uid_by_token)):
    """

    点对点的对话记录


    """
    channel = await Channel.get(form.id)
    if channel and channel.type != "group":
        await ChatDialogMessage.find({"uid": uid, "channel_id": form.id}).delete()
        return GenericResponseModel()
    else:
        return GenericResponseModel(code=1, message="error_parameter")


@router.post("/group_history_message", response_model=GenericResponseModel[List[ChatGroupMessageModel]],
             summary="历史消息")
async def group_history_message(form: HistoryPageRequestModel,
                                uid: str = Depends(get_uid_by_token)) -> GenericResponseModel:
    """如果channel是2个人的，则是我的channel


    如果channel是群聊，则是群聊消息"""

    channel_id = form.channel_id
    filter = {}
    channel = await Channel.get(form.channel_id)
    last_message_id = form.last_message_id
    outs: List[ChatGroupMessageModel] = []
    if channel:
        if channel.type == "group":

            sort = [("_id",-1)]
            sort = (+ChatGroupMessage.id)

            filter['channel_id'] = channel_id
            if last_message_id == "":
                last_message_id =  await ChatGroupUserMessagePosition.get_last_message_id(channel_id, uid)

            if last_message_id != "":
                filter['_id'] = {'$gt': last_message_id}
            print(filter)

            items = await ChatGroupMessage.find(filter).sort(sort).limit(100).to_list()
            for item in items:
                msg = {
                    "id": item.id,
                    "sender": uid,
                    "kind": item.kind,
                    "type": "group",
                    "content": item.content,
                    "channel_id": item.channel_id,
                    "create_at": item.create_at,
                }
                outs.append(msg)
            return GenericResponseModel(result=outs)
    else:
        return error_return(408, "bad_request")


@router.post("/dialog_history_message", response_model=GenericResponseModel[List[ChatDialogMessageModel]],
             summary="Dialogg历史消息")
async def dialog_history_message(form: HistoryPageRequestModel,
                                 uid: str = Depends(get_uid_by_token)):
    """如果channel是2个人的，则是我的channel


    如果channel是群聊，则是群聊消息"""

    filter = {"uid": uid}
    channel_id = form.channel_id
    channel = await Channel.get(form.channel_id)
    last_message_id = form.last_message_id
    outs: List[ChatDialogMessageModel] = []
    if channel:
        if channel.type != "group":

            sort = (+ChatDialogMessage.id)
            # sort = {"_id":-1}

            filter['channel_id'] = channel_id
            if last_message_id:
                filter['_id'] = {'$lt': last_message_id}


            items = await ChatDialogMessage.find(filter).sort(sort).limit(100).to_list()
            for item in items:
                vo = ChatDialogMessageModel(**item.model_dump())

                outs.append(vo)
            return GenericResponseModel(result=outs)
        else:
            sort = (+ChatGroupMessage.id)

            items = await ChatGroupMessage.find(filter).sort(sort).limit(100).to_list()
            for item in items:
                vo = ChatGroupMessageModel(**item.model_dump())

                outs.append(vo)
    raise HTTPException(408, "bad_request")


@router.post("/search_user", response_model=GenericResponseModel[List[UserInfoModel]], summary="搜索用户")
async def search_user(form: SearchModel):
    q = form.q
    q = q.strip()
    user = await User.get(q)
    outs: List[UserInfoModel] = []
    if user is not None:
        user.avatar = user.get_avatar()
        o = UserInfoModel(**user.model_dump())
        outs.append(o)
    else:
        # user = await User.find_one({"$and":[{"username":q},{"email":q}]})
        user = await User.find_one({"username": q})
        if user is not None:
            user.avatar = user.get_avatar()
            o = UserInfoModel(**user.model_dump())
            outs.append(o)
        # else:
        #     filter = {
        #         "username":{
        #             "$regex": "/*"+q+"*/",
        #             "options":"i"
        #         }
        #     }
        #     items = await User.find(filter).to_list()
        #     for item in items:
        #         o = UserInfoModel(**item.model_dump())
        #         outs.append(o)
    print(outs)
    return success_return(outs)


@router.post("/search_group", response_model=GenericResponseModel[List[ChanndelItemModel]], summary="搜索群")
async def search_group(form: SearchModel):
    q = form.q
    channel = await Channel.find_one({"_id": q, "type": "group"})
    outs: List[ChanndelItemModel] = []
    if channel is not None:
        o = ChanndelItemModel(**channel.model_dump())
        if o.logo == "":
            o.logo = CONFIG.default_channel_avatar

        outs.append(o)

    # else:
    #     channel = await Channel.find_one({"name": q})
    #     if channel:
    #         o = GroupInfoModel(**channel.model_dump())
    #         outs.append(o)
    #     else:
    #         filter = {
    #             "name": {
    #                 "$regex": {
    #                     "/*" + q + "*/"
    #                 },
    #                 "options": "i"
    #             }
    #         }
    #         items = await Channel.find(filter).to_list()
    #         for item in items:
    #             o = GroupInfoModel(**item.model_dump())
    #             outs.append(o)
    return success_return(outs)


class UserFollowDetailModel(UserInfoModel):
    nickname: Optional[str] = ""
    username: Optional[str]  = ""
    memo: Optional[str]  = ""

    intro: str = ""
    pid: str = ""
    level: int = 0
    invite_num: int = 0
    user_type: str = ""
    channel_id: str = ""
    followed: bool = False
    can_chat: bool = False


@router.post("/user_detail", response_model=GenericResponseModel, summary="user detail")
async def user_detail(form: IDModel, uid: str = Depends(get_uid_by_token)):
    id = form.id
    user = await User.get(id)
    if user is not None:
        user.avatar = user.get_avatar()

        info = UserFollowDetailModel(**user.model_dump())
        item = await UserFollow.find_one({"uid": uid, "target": id})
        if item is not None:
            info.followed = True
        channel = await Channel.get_pair_channel(uid, id)
        if channel is not None:
            info.can_chat = True
            info.channel_id = channel.id
        contact = await Contact.find_one({"receiver": id, "uid": uid})
        if contact is not None:
            info.memo = contact.memo

        return success_return(info)
    else:
        return error_return(404, "no_such_user")


@router.post("/channel_info", response_model=GenericResponseModel, summary="频道信息")
async def channel_info(form: IDModel, uid: str = Depends(get_uid_by_token)):
    id = form.id
    channel = await Channel.get(id)
    if channel is not None:
        item = ChanndelItemModel(**channel.model_dump())
        if channel.type == "group":
            item.join_channel_link = CONFIG.invite_join_group_link+"/#invite/"+channel.id
            if item.logo == "":
                item.logo = CONFIG.default_channel_avatar
        if uid in channel.user_ids:
            item.user_in_channel = True
        if uid in channel.admin_ids:
            item.is_admin = True
        if channel.type == "pair":
            item.target = [t for t in channel.user_ids if t != uid][0]
            contact = await Contact.find_one({"receiver": item.target, "uid": uid})
            if contact is not None and contact.memo != "":
                item.name = contact.memo
        if item.name == "":
            userinfo = await User.get_info(item.target)
            if userinfo is not None:
                item.name = userinfo.username

        return success_return(item)
    else:
        return error_return(404, "no_such_channel")

from pydantic import BaseModel

class UserIDS(BaseModel):
    ids:List[str]

@router.post("/userinfo", response_model=GenericResponseModel[List], summary="用户信息")
async def userinfo(form: UserIDS, uid: str = Depends(get_uid_by_token)):
    outs = []
    for id in form.ids:
        user = await User.get_info(id)
        outs.append(user)
    return success_return(outs)


@router.post("/chat_configs", response_model=GenericResponseModel, summary="配置信息")
async def chat_configs(form: IDModel, uid: str = Depends(get_uid_by_token)):
    outs = {}
    channel_id = form.id
    channel = await Channel.get(channel_id)
    agent_ids = channel.agent_ids

    cmds = [{"id":1,"name":"wallet","cmd":'open_wallet','agent_id':'agent_1'},
            {"id":2,"name":"setting","cmd":'open_setting','agent_id':'agent_2'}]
    outs['cmd_list'] = cmds;
    outs['cmd_map']={
        "open_wallet":"agent_1",
        "open_setting":"agent_2"
    }
    outs['agents_ids'] = agent_ids

    return success_return(outs)


