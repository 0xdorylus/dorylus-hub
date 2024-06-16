from fastapi.security import APIKeyHeader
from fastapi import Depends, HTTPException, status
from .redishelper import get_redis



# 定义一个名为 X-Auth 的自定义头
api_key_header = APIKeyHeader(name="X-Auth", auto_error=False)
api_biz_key_header = APIKeyHeader(name="X-Biz-Auth", auto_error=False)

async def get_uid_by_token(x_auth: str = Depends(api_key_header)):
    if x_auth:
        redis = await get_redis()
        uid = await redis.get(x_auth)
        if uid:
            k = "login:"
            # redis.inc()
            return uid
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid X-Auth",
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid X-Auth Header",
        )


async def get_biz_uid_by_token(x_auth: str = Depends(api_biz_key_header)):
    if x_auth:
        redis = await get_redis()
        uid = await redis.get(x_auth)
        if uid:
            return uid
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid X-Biz-Auth",
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid X-Biz-Auth Header",
        )