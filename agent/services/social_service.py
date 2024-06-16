import json
import logging

import socketio

from agent.errors.biz import AgentNotFoundError
from agent.models.agent import Agent
from agent.models.assistant import Assistant, CreateAssistantModel
from agent.models.base import GenericResponseModel
from agent.models.chat_message import ChatMessage, ChatDialogMessage, ChatDialogMessageModel, ChatGroupMessage, \
    ChatGroupMessageModel, ChatGroupUserMessagePosition
from agent.models.contact import Contact
from agent.models.conversation import Conversation
from agent.models.notice import Notice
from agent.models.request_response_model import CreateGroupModel, GroupDetailModel, UpdateGroupModel, \
    FinishResponseModel, \
    MessageModel, CreateAgentModel
from agent.models.subscribe import Subscription
from agent.models.user import User
from agent.models.channel import Channel
from fastapi import HTTPException

from agent.services.agent_service import AgentService
from agent.services.ai_hub_service import AIHubService
from agent.services.feed_service import FeedService
from agent.services.llm_service import LLMService
from agent.utils.common import encode_input, op_log, get_unique_id, error_return, success_return
from agent.config import CONFIG
from agent.utils.redishelper import get_redis

mgr = socketio.AsyncRedisManager(url=CONFIG.sio_redis_url)
sio = socketio.AsyncServer(
    async_mode="asgi", cors_allowed_origins="*", client_manager=mgr
)

llm_service = LLMService()


async def ask_llm(sid, channel_id, sender, receiver, content, reply_id):
    if CONFIG.use_open_router:
        return await AIHubService.send(sio, sid, channel_id, sender, receiver, content, reply_id)
    else:
        return await llm_service.send(sio, sid, channel_id, sender, receiver, content, reply_id)


class SocialService:

    @classmethod
    async def get_messagge(cls, sid: str, id: str):
        doc = await ChatDialogMessage.get(id)
        if doc:
            response = ChatDialogMessageModel(**doc.model_dump())
            if doc.sender != doc.uid:
                is_user = False
            else:
                is_user = True
            response.is_user = is_user
            resp = response.model_dump_json()
            r = json.loads(resp)
            await sio.emit("get_message", r, sid)

    async def get_receiver_type(receiver):
        object = await Assistant.find_one(Assistant.id == receiver)
        receiver_type = ""
        if object:
            receiver_type = "ai"
        else:
            user = await User.find_one(User.id == receiver)
            if user:
                receiver_type = "human"
            else:
                channel = await Channel.find_one(User.id == receiver)
                if channel:
                    receiver_type = "group"
                else:
                    raise HTTPException()
                    receiver_type = None
        return receiver_type

    @classmethod
    async def send(cls, uid: str, msg_items: MessageModel, source="ws"):
        """
            人发给机器

        :param uid:
        :param msg_items:
        :return:
        """
        redis = await get_redis()
        sid = await redis.get(f"socket:{uid}")

        channel_id = msg_items.channel_id
        receiver = msg_items.receiver

        channel = await Channel.find_one(Channel.id == channel_id)
        if not channel:
            response = GenericResponseModel(code=404, message="channel_not_found")
            await sio.emit("error", response, sid)
            return response

        if uid not in channel.user_ids:
            return GenericResponseModel(code=403, message="sender_fail")
        channel_type = channel.type
        if channel_type == "p2p" or channel_type == "p2m" or channel_type == "m2m":
            if receiver not in channel.user_ids:
                return GenericResponseModel(code=403, message="receiver_fail")

        if channel_type == "p2p":
            """
                人和人
            """
            doc = {
                "id": get_unique_id(),
                "uid": uid,
                "sender": uid,
                'receiver': receiver,
                "content": msg_items.content,
                "channel_id": channel_id,
                "kind": msg_items.kind,
            }
            sender_doc = await ChatDialogMessage(**doc).create()
            doc = {
                "id": get_unique_id(),
                "uid": receiver,
                "sender": uid,
                'receiver': receiver,
                "content": msg_items.content,
                "channel_id": channel_id,
                "kind": msg_items.kind,
            }
            receiver_doc = await ChatDialogMessage(**doc).create()

            await Conversation.set_p2p_last_message(uid, channel_id, receiver, msg_items.content)

            for tmpuid in channel.user_ids:
                sid = await redis.get(f"socket:{tmpuid}")
                if sid:
                    if tmpuid == uid:
                        response = ChatDialogMessageModel(**sender_doc.model_dump())
                        resp = response.model_dump_json()
                        r = json.loads(resp)

                        await sio.emit("text_chat", r, sid)
                    else:
                        response = ChatDialogMessageModel(**receiver_doc.model_dump())
                        resp = response.model_dump_json()
                        r = json.loads(resp)
                        await sio.emit("text_chat", r, sid)



        elif channel_type == "p2m":
            """
                人和机器
                
                发送不需要两份
            """
            # 发送的消息
            doc = {
                "id": get_unique_id(),
                "uid": uid,
                "sender": uid,
                'receiver': receiver,
                "content": msg_items.content,
                "channel_id": channel_id,
                "kind": msg_items.kind,
            }
            sender_doc = await ChatDialogMessage(**doc).create()

            # AI回复的消息
            doc = {
                "id": get_unique_id(),
                "uid": uid,
                "sender": receiver,
                'receiver': uid,
                "content": "",
                "ref_id": sender_doc.id,
                "channel_id": channel_id,
                "kind": "text",
            }
            answer_doc = await ChatDialogMessage(**doc).create()

            sid = await redis.get(f"socket:{uid}")
            if sid:
                response = ChatDialogMessageModel(**answer_doc.model_dump())

                response.is_user = False
                resp = response.model_dump_json()
                r = json.loads(resp)

                await sio.emit("reply_message_created", r, sid)
                answer = await  ask_llm(sid, channel_id, uid, receiver, msg_items.content, answer_doc.id)
                # print(answer)
                if answer:
                    await ChatDialogMessage.find_one(ChatDialogMessage.id == answer_doc.id).update(
                        {"$set": {"content": answer, "complete": True}})
                    answer_doc.content = answer
                    response = ChatDialogMessageModel(**answer_doc.model_dump())

                    response.is_user = False
                    resp = response.model_dump_json()
                    r = json.loads(resp)

                    await sio.emit("message_replied", r, sid)
                    await Conversation.set_ai_last_messae(uid, answer_doc.sender, answer)
                    await ChatDialogMessage.set_answer(sender_doc.id, answer)





        elif type == "group":
            """
            群
            """
            # 发送的消息
            doc = {
                "id": get_unique_id(),
                "sender": uid,
                'receiver_list': channel.user_ids,
                "content": msg_items.content,
                "channel_id": channel_id,
                "kind": msg_items.kind,
            }
            sender_doc = await ChatGroupMessage(**doc).create()
            await Conversation.set_group_last_messae(channel_id, msg_items.content)

            for tmpuid in channel.user_ids:
                sid = await redis.get(f"socket:{tmpuid}")
                response = ChatGroupMessageModel(**sender_doc)
                resp = response.model_dump_json()
                r = json.loads(resp)

                if sid:
                    await ChatGroupUserMessagePosition.update_last_message_id(channel_id, uid, sender_doc.id)
                    await sio.emit("text_chat", r, sid)

        return GenericResponseModel()

    async def update_group(self, uid, form: UpdateGroupModel):
        channel = await Channel.get(form.id)
        if channel.uid != uid:
            raise HTTPException(403, "Forbidden")
        else:
            filter_items = {k: v for k, v in form.model_dump().items() if
                            (v is not None and v != "" and v != [] and v != {})}
            # print(filter_items)
            update_query = {"$set": {
                field: value for field, value in filter_items.items()
            }}
            await  Channel.find_one(Channel.id == form.id).update(update_query)
            vo = await Channel.get(form.id)
            await op_log("update assistant: %s", form.id)
            return GroupDetailModel(**vo.model_dump())

    @classmethod
    async def subscribe_agent(cls, uid: str, agent_id: str):
        channel = await Channel.get_ai_channel(uid, agent_id)
        if channel is not None:
            return channel
        agent = await Agent.get(agent_id)
        if agent is None:
            # return None
            raise AgentNotFoundError("agent_not_found")
        await op_log("subscribe_agent uid %s %s ", uid, agent_id)

        await Subscription.subscribe_agent(uid, agent_id)
        # await Agent.operate_counter(agent_id, "subscribed_num", 1)

        channel = await Channel.create_ai_channel(uid, agent_id)
        await Conversation.add_agent_conversation(uid, agent_id, channel.id)
        return channel

    async def unsubscribe_assistant(self, uid: str, assistant_id: str):
        await op_log("unsubscribe_assistant uid %s %s ", uid, assistant_id)
        subscribed = await Subscription.is_subscribed_assistant(uid, assistant_id)
        if not subscribed:
            raise HTTPException(405, "not_subscribed")

        ret = await User.find_one(User.id == uid).update({"$pull": {User.assistant_ids: {"$in": [assistant_id]}}})
        logging.info(ret)
        await Subscription.unsubscribe_assistant(uid, assistant_id)
        await Channel.drop_ai_channel(uid, assistant_id)
        await Conversation.drop_assistant_conversation(uid, assistant_id)

    async def push(self, uid):
        redis = await get_redis()
        sid = await redis.get(f"socket:{uid}")
        if sid:
            pass
        else:
            return False

    async def send_img(self, channel_id, assistant_id, uid, url):
        redis = await get_redis()
        sid = await redis.get(f"socket:{uid}")
        if sid:

            content = {
                "url": url,
                "acl": "level:50"
            }
            doc = {
                "id": get_unique_id(),
                "uid": uid,
                "sender": assistant_id,
                'receiver': uid,
                "content": content,
                "channel_id": channel_id,
                "kind": "image",
            }
            sender_doc = await ChatDialogMessage(**doc).create()
            response = ChatDialogMessageModel(**sender_doc.model_dump())
            resp = response.model_dump_json()
            r = json.loads(resp)
            await sio.emit("text_chat", r, sid)
            return True
        else:
            logging.error("UID %s is not online", uid)
            return False

    async def send_text(self, channel_id, assistant_id, uid, url):
        redis = await get_redis()
        sid = await redis.get(f"socket:{uid}")
        if sid:

            content = {
                "url": url,
                "acl": "level:50"
            }
            doc = {
                "id": get_unique_id(),
                "uid": uid,
                "sender": assistant_id,
                'receiver': uid,
                "content": content,
                "channel_id": channel_id,
                "kind": "text",
            }
            sender_doc = await ChatDialogMessage(**doc).create()
            response = ChatDialogMessageModel(**sender_doc.model_dump())
            resp = response.model_dump_json()
            r = json.loads(resp)
            await sio.emit("text_chat", r, sid)
            return True
        else:
            logging.error("UID %s is not online", uid)
        return False

    async def send_notice(self, uid, content):
        """
        系统提示

        """
        redis = await get_redis()
        sid = await redis.get(f"socket:{uid}")
        if sid:

            doc = {
                "id": get_unique_id(),
                "uid": uid,
                "content": content,
                "kind": "text",
            }
            sender_doc = await Notice(**doc).create()
            # response = ChatDialogMessageModel(**sender_doc.model_dump())
            # resp = response.model_dump_json()
            # r = json.loads(resp)
            await sio.emit("notice", doc, sid)
            return True
        else:
            logging.error("UID %s is not online", uid)
        return False

    async def send_channel_notice(self, uid, content, channel_id):
        """
        系统提示

        """
        redis = await get_redis()
        sid = await redis.get(f"socket:{uid}")
        if sid:

            doc = {
                "id": get_unique_id(),
                "uid": uid,
                "content": content,
                "channel_id": channel_id,
                "kind": "text",
            }
            sender_doc = await Notice(**doc).create()
            # response = ChatDialogMessageModel(**sender_doc.model_dump())
            # resp = response.model_dump_json()
            # r = json.loads(resp)
            await sio.emit("notice", doc, sid)
            return True
        else:
            logging.error("UID %s is not online", uid)
        return False

    @classmethod
    async def create_group(cls, uid, form: CreateGroupModel):
        form.user_ids.append(uid)
        data = form.model_dump()
        data['uid'] = uid
        data['type'] = "group"
        data['admin_ids'] = [uid]
        group = await Channel.find_one({"type": "group", "name": form.name})
        if group:
            return error_return(403, "already_has_this_group_name")

        channel = await Channel(**data).create()
        if form.create_agent:
            """
                自动创建AI角色
            """
            agentForm = CreateAgentModel(username="i-" + form.name)
            ret = await AgentService.create_agent(uid, agentForm)
            print(ret)
            if ret.code == 0:
                agent = ret.result['agent']
                user = ret.result['user']

                channel.agent_ids.append(agent.id)
                channel.user_ids.append(user.id) #用户增加一个机器人
                await channel.save()

                await FeedService.follow(uid, user.id)

                logging.info("create agent succ")


            else:
                logging.error("create agent error")
        else:
            print("not create agent")

        await Conversation.add_group_conversation(uid, channel.id, channel.name)

        return success_return(GroupDetailModel(**channel.model_dump()))
