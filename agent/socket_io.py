import json

import socketio
from urllib import parse
import logging

from agent.errors.biz import UserNotInChannel
from agent.models.channel import Channel
from agent.models.chat_message import ChatDialogMessage
from pydantic import ValidationError

from agent.models.request_response_model import MessageModel
from agent.models.user_channel import UserChannel
from agent.models.user_login import UserLogin
from agent.services.event_service import EventService

from agent.services.social_service import SocialService
from  pymongo.errors import DuplicateKeyError

import os

from dotenv import load_dotenv

from agent.utils.common import get_current_time

load_dotenv()
sio_redis_url = os.getenv("SIO_REDIS_URL")

logging.basicConfig(filename='agent.log', level=logging.INFO)
from agent.config import CONFIG
# comment/edit line 5 if you don't want use redis or using other message queue
# see https://python-socketio.readthedocs.io/en/latest/server.html#using-a-message-queue
mgr = socketio.AsyncRedisManager(url=sio_redis_url)
sio = socketio.AsyncServer(
    async_mode="asgi", cors_allowed_origins="*", client_manager=mgr
)
from agent.utils.redishelper import get_redis
from datetime import datetime
@sio.event
async def connect(sid, environ):
    pass

@sio.event
async def get_message(sid, params):
    if "id" in params:
        id = params['id']
        await SocialService.get_messagge(sid,id)

@sio.event
async def login(sid,params):
    # print(params)
    # print(type(params))

    # params = json.loads(message)
    if "token" in params:
        # print(params)
        redis = await get_redis()
        token = params['token']
        uid = await redis.get(token)
        if uid:
            await redis.set(f"socket:{uid}", sid)
            await redis.set(f"socket:{sid}", uid)
            await redis.set(f"socket:{sid}:token", token)

            date_time = datetime.now().strftime("%Y%m%d")
            flag = await redis.get(f"login:{date_time}:{uid}")
            if not flag:
                doc = {
                    "uid":uid,
                    "ymd":date_time
                }
                await UserLogin(**doc).create()
            else:
                await UserLogin.find_one( {
                    "uid":uid,
                    "ymd":date_time
                }).update({"$inc":{"num":1}})

            await redis.setex(f"login:{date_time}:{uid}",60*86400,1)
            await sio.emit('message', f'{token}连线成功！')

        else:
            logging.error("token not found:"+token)
            await sio.emit('error', 'uid not found ')
            return False

    else:
        await sio.emit('message', 'token not in params')
        return False

    logging.info('login '+sid+ " succ")


@sio.event
async def disconnect(sid):
    redis = await get_redis()
    uid = await redis.get(f"socket:{sid}")
    await redis.delete(f"socket:{sid}")
    await redis.delete(f"socket:{uid}")
    await redis.delete(f"socket:{sid}:token")
    logging.info('disconnect '+sid)


@sio.event
async def message_sent(sid, message):
    await sio.emit("reply_message_created", {})



@sio.event
async def ack(sid, items):
    """
    确认收到消息
    """
    id = items['id']
    type = items['type']
    if type == "group":
        pass
        # await ChatGroupMessage.ack(id)
    else:
        await ChatDialogMessage.ack(id)

@sio.event
async def read(sid, items):
    pass


@sio.event
async def message(sid, items):
    redis = await get_redis()
    uid = await redis.get(f"socket:{sid}")
    logging.info("text_chat => uid: %s",uid)
    if uid:

         try:
             msg_items = MessageModel(**items)
             await SocialService.send(uid,msg_items)

         except ValidationError as e:
             logging.error(e.errors())
             # print(e)
             await sio.emit("error", {'message': "ValidationError"},sid)

         except DuplicateKeyError as e:
             # print(e)
             logging.error(e.errors())

             await sio.emit("error", {'message':"ID Duplicate"},sid)
    else:
        logging.error("user need to login")
        await sio.emit("auth_fail", {'sid': sid},sid)

@sio.event
async def first_join_channel(sid, items):
    redis = await get_redis()
    uid = await redis.get(f"socket:{sid}")
    if uid:
         try:
             msg_items = MessageModel(**items)
             if msg_items.kind == "join_channel":
                 channel_id = msg_items.channel_id
                 channel = await Channel.find_one({"_id": channel_id, "user_ids": {"$in": [uid]}})
                 if not channel:
                    await sio.emit("error", {'message': "user_not_in_channel"}, sid)
                 else:
                     is_first_join = await UserChannel.is_first_join(uid, channel_id)
                     if is_first_join:
                         await UserChannel.create(uid=uid, channel_id=channel_id, join_at=get_current_time())
                         if channel_id == CONFIG.system_agent_id:  # 默认的系统频道
                             await EventService.first_onboard_event(uid,channel_id,sid)
                         else:
                             pass


         except ValidationError as e:
             logging.error(e.errors())
             # print(e)
             await sio.emit("error", {'message': "ValidationError"},sid)

         except DuplicateKeyError as e:
             # print(e)
             logging.error(e.errors())

             await sio.emit("error", {'message':"ID Duplicate"},sid)
    else:
        logging.error("user need to login")
        await sio.emit("auth_fail", {'sid': sid},sid)

