from fastapi import FastAPI
from redis import asyncio as aioredis
import secrets
import redis


def get_sync_redis():
    r = redis.Redis(host='localhost', port=6379, db=0,decode_responses=True)
    return r

# 连接Redis
async def get_redis():
    redis = await aioredis.from_url("redis://localhost",  db=0, decode_responses=True)
    return redis




async def get_nonce(target):
    redis = await get_redis()
    nonce = secrets.token_hex(16)
    await redis.set(target, nonce)
    return nonce

async def check_nonce_used(target, nonce):
    redis = await get_redis()
    nonce = await redis.get(target)
    return nonce

async def check_nonce(target, nonce):
    redis = await get_redis()
    nonce = await redis.get(target)
    return nonce

async def publish(channel, message):
    redis = await get_redis()
    await redis.publish(channel, message)