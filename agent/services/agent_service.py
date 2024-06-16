import logging

import httpx as httpx

from agent.connection import get_next_id
from agent.models.agent import Agent
from agent.models.assistant import AssistantModel, Assistant, CreateAssistantModel
from agent.models.base import GenericResponseModel
from agent.models.channel import Channel
from agent.models.conversation import Conversation
from agent.models.request_response_model import CreateAgentModel,CreateAssistantResponseModel, GroupDetailModel, CreateGroupModel
from agent.models.system_tag import SystemTag

from agent.models.user import User
from agent.services.acl_service import AclService

import openai, os

from agent.utils.common import error_return, success_return, encode_input, op_log, fill_model_from_obejct, get_unique_id

from fastapi import FastAPI, HTTPException

os.environ["OPENAI_API_KEY"] = ""
openai.api_key = ""

default_callback_url = "http://127.0.0.1:9301/AI/Inner/submitTask"


class AgentService:
    llm: None

    def __init__(self) -> None:
        self.base_storage_path = '/opt/dorylus/knowledge-storage'

    @classmethod
    async def create_agent(self, uid, form: CreateAgentModel):
        # print("create_agent",uid)
        # print(form)
        vo = await Agent.find_one(Agent.username == form.username)
        if vo is not None:
            return error_return(403, "name_exists")


        acl = await AclService.user_can_create_agent(uid)
        if acl:

            # //过滤掉垃圾数据
            form.tag_ids = await SystemTag.filter_tags(form.tag_ids)
            data = form.model_dump()
            data['uid']  = uid
            agent = await Agent(**data).create()

            id = await get_next_id("agent")

            # //创建一个默认的用户
            doc = {
                "owner": uid, #主账号
                "username": "agent-" + form.username+str(id),
                "nickname":form.nickname,
                "user_type": "agent",
                "agent_id": agent.id,
            }
            user = await User(**doc).create()

            user.update_avatar()
            await User.find_one(User.id == uid).update({"$addToSet": {User.agent_ids: agent.id}})

            # await SocialService.subscribe_agent(uid, agent.id)
            #create user and agent
            return success_return({"user":user, "agent":agent })
        else:
            return error_return(403, "User can not create agent")

    @classmethod
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
    async def create_group_agent(cls, uid, assistatForm: CreateAssistantModel) -> CreateAssistantResponseModel:
        vo = await Agent.find_one(Agent.name == assistatForm.name)
        if vo:
            raise HTTPException(status_code=403, detail="name_exists")
        else:
            acl = await AclService.user_can_create_agent(uid)
            if acl:
                # //过滤掉垃圾数据
                assistatForm.tag_ids = await SystemTag.filter_tags(assistatForm.tag_ids)
                data = assistatForm.model_dump()
                data['uid'] = uid
                agent = await Agent(**data).create()



                return agent
            else:
                raise HTTPException(status_code=403, detail="User can not crreate assistant")

    @classmethod
    async def create_group(cls, uid, form: CreateGroupModel):
        form.user_ids.append(uid)
        data = form.model_dump()
        data['uid'] = uid
        data['type'] = "group"
        data['admin_ids'] = [uid]
        channel = await Channel(**data).create()
        if form.create_agent:
            """
                自动创建AI角色
            """
            assistatForm = CreateAssistantModel(name="annie@" + form.name)
            assistant = await AssistantService.create_group_assistant(uid, assistatForm)
            channel.assistant_ids.append(assistant.id)
            channel.save()

            # assistant_ids

            pass

        await Conversation.add_group_conversation(uid, channel.id)

        return GroupDetailModel(**channel.model_dump())

