import json

from agent.config import CONFIG
from agent.utils.common import get_current_time, get_unique_id
import socketio

mgr = socketio.AsyncRedisManager(url=CONFIG.sio_redis_url)
sio = socketio.AsyncServer(
    async_mode="asgi", cors_allowed_origins="*", client_manager=mgr
)

class EventService:
    def __init__(self):
        pass


    @classmethod
    async def first_onboard_event(cls,uid,channel_id,sid):
        """
            用户第一次加入系统频道的时候，发送欢迎消息
        """
        system_agent_uid = CONFIG.system_agent_id
        resp = {
            "id": get_unique_id(),
            "uid":uid,
            "sender": system_agent_uid,
            'receiver': uid,
            "channel_id":channel_id,
            "kind":"text",
            "content":"Welcome to dorylus agent metaverse!",
            "created_at":get_current_time()
        }
        r = json.loads(resp)
        await sio.emit("message", r, sid)


        content  = {
            "title": "For better chat,please choose language!",
        }
        resp = {
            "id": get_unique_id(),
            "uid": uid,
            "sender": system_agent_uid,
            'receiver': uid,
            "channel_id": channel_id,
            "kind": "choice",
            "content": "Welcome to dorylus agent metaverse!",
            "created_at": get_current_time()
        }
        r = json.loads(resp)
        await sio.emit("message", r, sid)


    def create(self, event):
        return self.event_repository.create(event)

    def get(self, event_id):
        return self.event_repository.get(event_id)

    def get_all(self):
        return self.event_repository.get_all()

    def update(self, event):
        return self.event_repository.update(event)

    def delete(self, event_id):
        return self.event_repository.delete(event_id)