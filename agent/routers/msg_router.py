from fastapi import APIRouter, Depends, Response

from agent.models.assistant import AssistantModel, Assistant, CreateAssistantModel
from agent.models.base import GenericResponseModel
from agent.services.assistant_service import AssistantService
from agent.utils.x_auth import get_uid_by_token

router = APIRouter(prefix="/message", tags=["message"])

# @router.get("/me")
# async def get_self():
#     """Get current user"""
#     return {"uid": uid}
#
# @router.post("/me")
# async def send(askForm:AskForm):
#     """Get current user"""
#     return {"uid": uid}
#
# @router.post("/query"):
# async def query(assistant_id:str):
#     """Get current user"""
#
#     return {"uid": uid}


