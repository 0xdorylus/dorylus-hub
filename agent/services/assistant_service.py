import logging

import httpx as httpx

from agent.models.assistant import AssistantModel, Assistant, CreateAssistantModel
from agent.models.base import GenericResponseModel
from agent.models.channel import Channel
from agent.models.conversation import Conversation
from agent.models.request_response_model import CreateAssistantResponseModel, GroupDetailModel, CreateGroupModel
from agent.models.system_tag import SystemTag

from agent.models.user import User
from agent.services.acl_service import AclService

import openai, os

from agent.services.social_service import SocialService
from agent.utils.common import error_return, success_return, encode_input, op_log, fill_model_from_obejct

from fastapi import FastAPI, HTTPException

os.environ["OPENAI_API_KEY"] = ""
openai.api_key = ""

default_callback_url = "http://127.0.0.1:9301/AI/Inner/submitTask"


class AssistantService:
    llm: None

    def __init__(self) -> None:
        self.base_storage_path = '/deploy/dorylus/knowledge-storage'

    async def create_assistant(self, uid, assistatForm: CreateAssistantModel) -> CreateAssistantResponseModel:
        vo = await Assistant.find_one(Assistant.name == assistatForm.name)
        if vo:
            raise HTTPException(status_code=403, detail="name_exists")
        else:
            acl = await AclService.user_can_create_agent(uid)
            if acl:
                # //过滤掉垃圾数据
                assistatForm.tag_ids = await SystemTag.filter_tags(assistatForm.tag_ids)
                data = assistatForm.model_dump()
                data['uid'] = uid
                assistant = await Assistant(**data).create()

                assistant_info = CreateAssistantResponseModel(**assistant.model_dump())
                print(assistant_info)
                social_service = SocialService()
                await social_service.subscribe_agent(uid, assistant.id)

                return assistant_info
            else:
                raise HTTPException(status_code=403, detail="User can not crreate assistant")

    async def update_assistant(self, uid: str, update_form: AssistantModel) -> GenericResponseModel:
        assistant = await Assistant.find_one(Assistant.id == update_form.id)
        if assistant:
            if (assistant.uid != uid):
                raise HTTPException(status_code=403, detail="assistant_owner_error")

            if update_form.name:
                vo = await Assistant.find_one(Assistant.name == update_form.name)
                if (vo and vo.uid != uid):
                    raise HTTPException(status_code=403, detail="name_already_exists")

            update_form.tag_ids = await SystemTag.filter_tags(update_form.tag_ids)

            req = {k: v for k, v in update_form.model_dump().items() if (v is not None and v != "" and v != [])}
            update_query = {"$set": {
                field: value for field, value in req.items()
            }}
            await  Assistant.find_one(Assistant.id == update_form.id).update(update_query)
            await op_log("update assistant: %s", assistant.id)
            return update_form

        else:
            raise HTTPException(status_code=403, detail="assistant_not_exist")

    @classmethod
    async def create_group_assistant(cls, uid, assistatForm: CreateAssistantModel) -> CreateAssistantResponseModel:
        vo = await Assistant.find_one(Assistant.name == assistatForm.name)
        if vo:
            raise HTTPException(status_code=403, detail="name_exists")
        else:
            acl = await AclService.user_can_create_agent(uid)
            if acl:
                # //过滤掉垃圾数据
                assistatForm.tag_ids = await SystemTag.filter_tags(assistatForm.tag_ids)
                data = assistatForm.model_dump()
                data['uid'] = uid
                assistant = await Assistant(**data).create()

                assistant_info = CreateAssistantResponseModel(**assistant.model_dump())
                print(assistant_info)
                social_service = SocialService()
                await social_service.subscribe_agent(uid, assistant.id)

                return assistant_info
            else:
                raise HTTPException(status_code=403, detail="User can not crreate assistant")

    @classmethod
    async def create_group(cls, uid, form: CreateGroupModel):
        form.user_ids.append(uid)
        data = form.model_dump()
        data['uid'] = uid
        data['type'] = "group"
        data['admin_ids'] = [uid]
        group = await Channel.find_one({"type": "group", "name": form.name})
        if group:
            return error_return(403, "already_has_this_group_name")

        channel = await Channel(**data).create()
        if form.create_agent:
            """
                自动创建AI角色
            """
            assistatForm = CreateAssistantModel(name="annie@" + form.name)
            assistant = await AssistantService.create_group_assistant(uid, assistatForm)
            channel.agent_ids.append(assistant.id)
            channel.save()

            pass

        await Conversation.add_group_conversation(uid, channel.id)

        return success_return(GroupDetailModel(**channel.model_dump()))
