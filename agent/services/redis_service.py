from redis import asyncio as aioredis

import os
import logging

class RedisService:
    def __init__(self):
        self.redis_host = f"{os.environ.get('REDIS_HOST', 'redis://localhost')}"

    async def get_reids(self):
        return await aioredis.from_url(self.redis_host, encoding="utf-8", decode_responses=True)
