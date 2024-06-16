from fastapi import APIRouter, Depends, Response

from agent.models.base import GenericResponseModel
from agent.models.subscribe import Subscription
from agent.models.user import User
from agent.utils.common import success_return
from agent.utils.x_auth import get_uid_by_token

router = APIRouter(prefix="/nlp", tags=["nlp"])


#
#
# @router.post("/voice_to_text")
# async def voice_to_text(mainchain:str="BSC", uid: str = Depends(get_uid_by_token)):
#     """Get current user"""
#     return {"uid": uid}
#
# @router.post("/text_to_voice")
# async def text_to_voice(mainchain:str="BSC", uid: str = Depends(get_uid_by_token)):
#     """Get current user"""
#     return {"uid": uid}
#
# @router.post("/text_to_image")
# async def text_to_image(mainchain:str="BSC", uid: str = Depends(get_uid_by_token)):
#     """Get current user"""
#     return {"uid": uid}
#
# @router.post("/image_to_text")
# async def image_to_text(mainchain:str="BSC", uid: str = Depends(get_uid_by_token)):
#     """Get current user"""
#     return {"uid": uid}
#
#
# @router.post("/text_to_video")
# async def text_to_video(mainchain:str="BSC", uid: str = Depends(get_uid_by_token)):
#     """Get current user"""
#     return {"uid": uid}
#
# @router.post("/video_to_text")
# async def text_to_image(mainchain:str="BSC", uid: str = Depends(get_uid_by_token)):
#     """Get current user"""
#     return {"uid": uid}