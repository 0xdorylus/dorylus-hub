from agent.models.channel import Channel
from agent.models.user_social import UserFollow
from agent.utils.common import get_current_time


class SocketService:

    @classmethod
    async def push(cls,uid,msg):
        redis = await get_redis()
        await UserFollow.update_one({"uid": uid, "target": target}, {"$set": {"create_at": get_current_time()}}, upsert=True)
        item = await cls.find_one({"uid": target, "target": uid})
        if item is not None:
            await Channel.try_create_pair_channel(uid, target)