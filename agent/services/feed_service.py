import json
from typing import Dict

from agent.models.channel import Channel
from agent.models.contact import Contact
from agent.models.conversation import Conversation
from agent.models.notice import Notice
from agent.models.user import User
from agent.models.user_social import UserFollow, UserFollowNotice

from agent.websocket.socket_manager import manager


class FeedService:
    @classmethod
    async def send_notice(cls, uid, message):
        print("try send message:", uid)
        # print("uid:",uid)
        # print("message:",message)
        # print(manager)
        print("manager", manager)

        if manager is not None:
            return await manager.send(uid, message)
        return False

    @classmethod
    async def follow(cls, uid, target):
        item = await UserFollow.find_one({"uid": uid, "target": target})
        if item is not None:
            return True

        await UserFollow(uid=uid, target=target).create()
        # 发送关注提示消息
        user = await User.get_info(uid)
        s = json.dumps({
            "kind": "follow_notice",
            "content": {
                "uid": target,
                "username": user.username,
                "avatar": user.avatar,
            }
        })
        flag = await cls.send_notice(target, s)
        if not flag:
            await Notice(uid=target, kind="follow_notice",message=s).create()
            #发送关注提醒通知s
            # await UserFollowNotice(uid=target, src_uid=uid, src_username=user.username, src_avatar=user.avatar,
            #                        status="sent").create()

        # user = await User.get(uid)
        target_user = await User.get_info(target)
        if target_user is None:
            return

        # 如果对方是Agent，则直接加入会话
        if target_user.user_type == "agent":
            channel = await Channel.try_create_pair_channel(uid, target)
            info_user = await User.get_info(uid)
            target_user = await User.get_info(target)

            await Contact.add_pair_contact(uid, target, target_user.username, target_user.avatar, channel.id)
            await Conversation.add_friend_conversation(uid, target, channel.id)
        else: #对方是正常用户
            item = await UserFollow.find_one({"uid": target, "target": uid})
            if item is not None:
                channel = await Channel.get_pair_channel(uid, target)
                if channel is None:
                    channel = await Channel.try_create_pair_channel(uid, target)
                    info_user = await User.get_info(uid)
                    target_user = await User.get_info(target)
                    await Contact.add_pair_contact(uid, target, target_user.username, target_user.avatar, channel.id)
                    await Contact.add_pair_contact(target,uid,  user.username, user.avatar, channel.id)

                    await Conversation.add_friend_conversation(uid, target, channel.id)
                    await Conversation.add_friend_conversation(target, uid, channel.id)
    @classmethod
    async def unfollow(cls, uid: str, target: str):
        print("unfollow:", uid, target)
        await UserFollow.find_one({"uid": uid, "target": target}).delete()
        await Channel.try_drop_pair_channel(uid, target)
