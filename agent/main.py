import datetime
import json
from typing import List, Dict, Optional, Any

from fastapi import FastAPI, Request, Depends
import os

from pydantic_core import ValidationError
from datetime import datetime, timedelta

from .config import CONFIG
from .database import init_db
from .errors.base import BaseError
from .models.base import GenericResponseModel
from .models.channel import Channel
from .models.chat_message import ChatDialogMessageModel, ChatDialogMessage, ChatGroupMessage, ChatMessagePosition
from .models.conversation import Conversation
from .models.notice import Notice
from .models.subscribe import Subscription
from fastapi import Cookie, Depends, FastAPI, Request, Query, WebSocket, status

from .models.user import User
from .models.user_acheievements import UserAchievement, AchievementItem, Achievement
from .routers import agent_router, notice_router, lottery_router, pay_router, contact_router, acl_router, \
    pay_router, \
    achieve_router, asset_router, help_router, article_router, tool_router, admin_router, nlp_router, user_router, \
    auth_router, fs_router, assistant_router, msg_router, social_router, feed_router, app_router
# fs, contract,brain,admin
import logging

from .services.ai_hub_service import AIHubService
from .services.llm_service import LLMService
from .socket_io import sio
import socketio
from fastapi.staticfiles import StaticFiles
from fastapi.security.api_key import APIKeyHeader
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import FastAPI, HTTPException
from fastapi import BackgroundTasks

from .utils.common import get_current_time
from .utils.redishelper import get_sync_redis, get_redis
from pytz import timezone
from apscheduler.triggers.cron import CronTrigger

from .utils.x_auth import get_uid_by_token

app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, WebSocket, WebSocketDisconnect


async def login_stat_job():
    redis = get_sync_redis()
    date_time = datetime.now().strftime("%Y%m%d")
    items = redis.keys(f"login:{date_time}:*")
    current_datetime = datetime.now()
    for item in items:
        print(item)
        tmpitmes = item.split(":")
        uid = tmpitmes[2]

        i = 1
        while i < 60:
            days_ago = (current_datetime - timedelta(days=i)).strftime("%Y%m%d")
            key = f"login:{days_ago}:{uid}"
            flag = redis.get(key)
            if i >= 60:
                await UserAchievement.get_achieve(uid, "Eternal Companion", 60)
            elif i >= 30:
                await UserAchievement.get_achieve(uid, "Devoted Fan", 30)
            elif i >= 14:
                await UserAchievement.get_achieve(uid, "Loyal User", 14)
            elif i >= 7:
                await UserAchievement.get_achieve(uid, "Streak Keeper", 7)
            elif i >= 3:
                await UserAchievement.get_achieve(uid, "Newcomer", 3)
            if not flag:
                print("jump out")

                break;
            i += 1


scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
trigger = CronTrigger(hour=1, minute=10, second=0)  # 每天晚上 20:00:00 执行任务
scheduler.add_job(login_stat_job, trigger)
scheduler.start()


@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()


# 允许所有来源的请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 自定义异常处理器
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=200,
        content={"code": exc.status_code, "message": exc.detail}
    )


@app.exception_handler(BaseError)
async def business_exception_handler(request, exc):
    return JSONResponse(
        status_code=200,
        content={"code": 400, "message": exc.message}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=200,
        content={"code": 400, "message": "Validation error", "details": exc.errors()}
    )


# @app.exception_handler(ValidationError)
# async def core_validation_exception_handler(request, exc):
#     return JSONResponse(
#         status_code=400,
#         content={"message": "Validation error", "details": exc.errors()}
#     )

# @app.exception_handler(TypeError)
# async def core_validation_exception_handler(request, exc):
#     return JSONResponse(
#         status_code=400,
#         content={"message": "Type error", "details": exc}
#     )


api_key_header = APIKeyHeader(name='X-Auth', auto_error=False)

app.mount("/static", StaticFiles(directory="static"), name="static")

# websocket
# event-driven

sio_asgi_app = socketio.ASGIApp(socketio_server=sio, other_asgi_app=app)
app.add_route("/socket.io/", route=sio_asgi_app, methods=["GET", "POST"])
app.add_websocket_route("/socket.io/", sio_asgi_app)

# from dotenv import load_dotenv
# os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
# os.environ["HUGGINGFACEHUB_API_TOKEN"] = os.getenv("HUGGINGFACEHUB_API_TOKEN")
logging.basicConfig(filename='agent.log', level=logging.INFO)
app.include_router(app_router.router)
app.include_router(auth_router.router)
app.include_router(fs_router.router)

app.include_router(user_router.router)
app.include_router(agent_router.router)

app.include_router(lottery_router.router)
app.include_router(pay_router.router)
app.include_router(contact_router.router)
app.include_router(achieve_router.router)
app.include_router(article_router.router)
app.include_router(help_router.router)
app.include_router(asset_router.router)
app.include_router(assistant_router.router)
app.include_router(tool_router.router)
app.include_router(acl_router.router)
app.include_router(social_router.router)
app.include_router(pay_router.router)

app.include_router(admin_router.router)

app.include_router(notice_router.router)
app.include_router(feed_router.router)


@app.get('/ping')
async def ping():
    print("finish!!")
    return {
        "message": "pong"
    }


@app.on_event("startup")
async def start_db():
    await init_db()
    print("init db success!!!")


from agent.websocket.socket_manager import WebSocketManager, ConnectionManager

socket_manager = WebSocketManager()

from agent.services.feed_service import manager, FeedService


async def get_cookie_or_token(
        websocket: WebSocket,
        session: Optional[str] = Cookie(None),
        token: Optional[str] = Query(None),
):
    if session is None and token is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
    return session or token


from agent.websocket.socket_manager import manager
from pydantic import BaseModel, Field
from pymongo.errors import DuplicateKeyError


class MessageModel(BaseModel):
    kind: str = Field("", min_length=1, max_length=32)
    content: Any = Field("", min_length=0, max_length=2048)
    channel_id: str = Field("", min_length=0, max_length=100)
    type: str = Field("", min_length=0, max_length=100)
    receiver: str = Field("", min_length=0, max_length=100)


class DialogMessage(BaseModel):
    pass

async def get_receiver_user_type(uid):
    redis  = await get_redis()
    user_key = f"user_{uid}"
    user_type = await redis.get(user_key)
    if user_type:
        return user_type
    else:
        user = await User.get_info(uid)
        await redis.set(user_key,user.user_type)
        return user.user_type


llm = LLMService()

async def ask_llm(channel_id, uid, agent_id, content, reply_id):
    if CONFIG.use_open_router:
        return await AIHubService.send(channel_id, uid, agent_id, content, reply_id)
    else:
        return await llm.send( channel_id, uid, agent_id, content, reply_id)

@app.websocket("/ws")
async def chat_websocket(websocket: WebSocket, token: str = Depends(get_cookie_or_token)):
    redis = await get_redis()
    uid = await redis.get(token)
    if uid is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    await manager.connect(uid, websocket)
    print("user  connected:", uid)
    try:
        while True:
            data = await websocket.receive_text()
            # print(data)
            if data == "~":
                await websocket.send_text("~")
            else:
                try:
                    items = json.loads(data)
                    bean = MessageModel(**items)

                    if bean.kind == "cmd": #执行命令,显示给自己
                        agent_id = bean.receiver
                        print(bean)

                        continue
                    elif bean.kind == "mention":
                        pass


                    if bean.type == "pair":
                        # avoid attack
                        receiver = await Channel.get_pairl_receiver(bean.channel_id, uid)
                        #创建发送者的消息记录
                        sender_doc = await ChatDialogMessage(uid=uid, channel_id=bean.channel_id, sender=uid,
                                                         kind=bean.kind,
                                                         receiver=receiver, content=bean.content, sent=True).create()
                        question_id = sender_doc.id

                        #给接收者发送消息，如果接收者是agent，则直接发送，否则，需要判断是否可以发送
                        msg = {
                            "id": sender_doc.id,
                            "sender": uid,
                            "receiver": receiver,
                            "kind": bean.kind,
                            "type": bean.type,
                            "content": bean.content,
                            "is_self": False,
                            "channel_id": sender_doc.channel_id,
                            "create_at": sender_doc.create_at,
                        }

                        flag = await manager.send(receiver, json.dumps(msg))
                        if flag:
                            sent = True
                            notice = {
                                "uid": receiver,
                                "kind": "message_notice",
                                "content": {
                                    "channel_id":sender_doc.channel_id,
                                    "last_message_id":sender_doc.id
                                }
                            }
                            await manager.send(receiver, json.dumps(notice))
                        else:
                            sent = False
                        #接收方的消息小红点提示实现机制,用户有一个该频道最新消息id，推送到用户，有一个本地保存的确认消息id，两者不同则提示红点
                        # await ChatMessagePosition.update_last_message_id(sender_doc.channel_id, receiver, sender_doc.id)




                        # 给发送者发送消息，确保网络正常回显示
                        dialog = await ChatDialogMessage(uid=receiver, channel_id=bean.channel_id, sender=uid,
                                                         kind=bean.kind,
                                                         receiver=receiver, content=bean.content, sent=sent).create()
                        msg["id"] = dialog.id
                        # msg['is_self'] = True
                        await manager.send(uid, json.dumps(msg))

                        #如果接收者是agent，则直接发送，否则，需要判断是否可以发送

                        user_type = await get_receiver_user_type(receiver)
                        print("user_type:",user_type)
                        if user_type == "agent":
                            agent_id = receiver
                            #点对点的时候，直接等待agent反应
                            answer_doc = {
                                "uid": uid,
                                "sender": receiver,
                                'receiver': uid,
                                "content": "",
                                "ref_id": question_id,
                                "kind": bean.kind,
                                "channel_id": bean.channel_id
                            }
                            answer_dialog = await ChatDialogMessage(**answer_doc).create()
                            answer_doc["id"] = answer_dialog.id
                            await manager.send(uid, json.dumps(answer_doc))
                            answer = await ask_llm(bean.channel_id, uid, agent_id, bean.content, answer_dialog.id)
                            if answer:
                                # print("answer:",answer)
                                await ChatDialogMessage.find_one(ChatDialogMessage.id == answer_dialog.id).update(
                                    {"$set": {"content": answer, "complete": True}})
                                await ChatDialogMessage.set_answer(sender_doc.id,answer) #为了简化计算

                                #设置对话列表
                                await Conversation.set_ai_last_messae(uid, receiver, answer)

                                answer_doc['content'] = answer
                                answer_doc['kind'] = "message_replied"
                                await manager.send(uid, json.dumps(answer_doc))
                        else: #正常用户
                            if  bean.kind == "text":
                                await Conversation.set_p2p_last_message(receiver, uid, bean.content)





                    elif bean.type == "group":
                        receiver_list = await Channel.get_receiver_list(bean.channel_id, uid)
                        # print("group:",receiver_list,uid,bean.channel_id)
                        message = await ChatGroupMessage(uid=uid, channel_id=bean.channel_id, sender=uid,
                                                        kind=bean.kind,
                                                        receiver_list=receiver_list, content=bean.content,
                                                        sent=True).create()

                        msg = {
                            "id": message.id,
                            "sender": uid,
                            "kind": bean.kind,
                            "type": bean.type,
                            "content": bean.content,
                            "channel_id": message.channel_id,
                            "create_at": message.create_at,
                        }
                        data = json.dumps(msg)
                        notice = {
                            "uid": uid,
                            "kind": "message_notice",
                            "content": {
                                "channel_id": bean.channel_id,
                                "last_message_id": message.id
                            }
                        }
                        for tuid in receiver_list:
                            flag = await manager.send(tuid,data)
                            if flag:
                                notice['uid'] = tuid
                                await manager.send(tuid, json.dumps(notice))
                        # await manager.batch_send(receiver_list, json.dumps(msg))
                        if bean.kind == "text":
                            pass
                            # await ChatGroupMessage.s(bean.channel_id, bean.content)


                except ValidationError as e:
                    logging.error(e.errors())
                    # print(e)

                except DuplicateKeyError as e:
                    # print(e)
                    logging.error(e.errors())


    except WebSocketDisconnect as e:
        manager.disconnect(uid, websocket)


async def broadcast_message(websocket: WebSocket, message: str):
    for client in app.websockets.values():
        if client != websocket:
            await client.send_json({
                "type": "message",
                "username": "Server",
                "message": message
            })


@app.websocket("/api/v1/ws/{room_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, user_id: int):
    await socket_manager.add_user_to_room(room_id, websocket)
    message = {
        "user_id": user_id,
        "room_id": room_id,
        "message": f"User {user_id} connected to room - {room_id}"
    }
    await socket_manager.broadcast_to_room(room_id, json.dumps(message))
    try:
        while True:
            data = await websocket.receive_text()
            message = {
                "user_id": user_id,
                "room_id": room_id,
                "message": data
            }
            await socket_manager.broadcast_to_room(room_id, json.dumps(message))

    except WebSocketDisconnect:
        await socket_manager.remove_user_from_room(room_id, websocket)

        message = {
            "user_id": user_id,
            "room_id": room_id,
            "message": f"User {user_id} disconnected from room - {room_id}"
        }
        await socket_manager.broadcast_to_room(room_id, json.dumps(message))


from pydantic import BaseModel
import json


class ReceiverModel(BaseModel):
    uid: str
    content: str
    kind: str = None
    channel_id: str = None


@app.post("/send", response_model=GenericResponseModel, summary="发送推文")
async def send(form: ReceiverModel, feed_service: FeedService = Depends()):
    data = json.dumps(form.dict())
    await feed_service.send(form.uid, data)

    return GenericResponseModel(code=200, msg="success")


@app.post("/inner_send", response_model=GenericResponseModel, summary="发送消息")
async def inner_send(form: ReceiverModel, feed_service: FeedService = Depends()):
    data = json.dumps(form.dict())
    await feed_service.send(form.uid, data)
    return GenericResponseModel(code=200, msg="success")


@app.get("/test")
async def test():
    uid="uid"
    kind="notice"
    content="notice"
    data = await Notice.find_one({"uid":uid})
    print(data)
    if data is None:
        await Notice(uid=uid,kind=kind,content=content).create()
    else:
        data.kind = "notice"+str(get_current_time())
        await data.save()
    return {"code": 0, "message": "success", "result": None}



class NoticeModel(BaseModel):
    id: str
    uid: str
    kind: str
    message:str
    sign:str

@app.post("/try_send_notice", response_model=GenericResponseModel, summary="是否在线")
async def try_send_notice(form: NoticeModel):
    if form.sign == "welcome2024hellobabby":
        flag = await manager.send(form.uid,form.message)
        if flag:
            await Notice.find_one({"id":form.id}).update({"$set":{"sent":1}})
            return {"code": 0, "message": "success", "result": None}
        else:
            return {"code": 400, "message": "fail", "result": None}







