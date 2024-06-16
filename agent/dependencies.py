from fastapi import Header, HTTPException
from fastapi.security import OAuth2PasswordBearer
from fastapi import  Depends, HTTPException
from datetime import datetime, timedelta
from typing import Optional


async def get_token_header(x_token: str = Header()):
    if x_token != "x-auth":
        raise HTTPException(status_code=400, detail="X-Token header invalid")


async def get_query_token(token: str):
    if token != "jessica":
        raise HTTPException(status_code=400, detail="No Jessica token provided")
