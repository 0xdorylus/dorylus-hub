"""
Current user dependency
"""

from fastapi import Depends, HTTPException
from fastapi_jwt_auth import AuthJWT

from agent.models.user import User


async def current_user(auth: AuthJWT = Depends()) -> User:
    """Returns the current authorized user"""
    auth.jwt_required()
    user = await User.by_uid(auth.get_jwt_subject())
    if user is None:
        raise HTTPException(404, "Authorized user could not be found")
    return user