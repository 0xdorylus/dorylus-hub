import requests
import json

import openai
from agent.config import CONFIG
from agent.models.assistant import Girl

# CONFIG.open_router_key"
from agent.models.chat_message import ChatMessage, ChatDialogMessage
from agent.models.system_prompt import SystemPrompt
from agent.services.redis_service import RedisService


from agent.utils.redishelper import get_redis, get_sync_redis

from fastapi import BackgroundTasks

openai.api_base = "https://openrouter.ai/api/v1"
openai.api_key = ""
mythomax_key = ""
class AIHubService:


    # async def send(self,sio,sid,channel_id,sender,receiver,content,reply_id:str):

    @classmethod
    async def sync_send(cls,messages):



        print(messages)
        response = openai.ChatCompletion.create(
            model="gryphe/mythomax-l2-13b",  # Optional
            messages=messages,
            headers = {
                "Authorization": "Bearer "+mythomax_key,
                "HTTP-Referer": "https://api.dorylus.ai/",  # To identify your agent. Can be set to e.g. http://localhost:3000 for testing
                "X-Title": "AI Agent" # Optional. Shows on openrouter.ai
            },
            stream=False  # this time, we set stream=True
        )
        return response
    @classmethod
    async def send(cls,sio,sid,channel_id,sender,receiver,content,reply_id:str):
        messages = []
        #
        # system_prompt 是对 AI 模型的角色定义和输出约束
        # history 是历史的对话信息，包括用户问题和AI回复
        # message 是当前用户提问的问题

        system_prompt = await Girl.get_girl_prompt(receiver)

        if system_prompt:
            messages.append({"role": "system", "content" : system_prompt})
            messages.append({"role": "user", "content": system_prompt})

        history = await ChatDialogMessage.get_ai_history_pair(channel_id, sender)
        # print("history")
        # print(history)
        for item in history:
            # item[0] 是用户问题， item[1] 是AI回复
            # messages.append(HumanMessage(content=item[0]))
            messages.append({"role": "user", "content" :item[0]})
            messages.append({"role": "assistant", "content": item[1]})

            # messages.append(AIMessage(content=item[1]))
        # 最后是当前用户问题
        messages.append({"role": "user", "content" :content})
        #
        # print(messages)

        response = openai.ChatCompletion.create(
            model="gryphe/mythomax-l2-13b",  # Optional
            messages=messages,
            headers = {
                "Authorization": "Bearer "+mythomax_key,
                "HTTP-Referer": "https://api.dorylus.ai/",  # To identify your agent. Can be set to e.g. http://localhost:3000 for testing
                "X-Title": "AI Agent" # Optional. Shows on openrouter.ai
            },
            stream=True  # this time, we set stream=True
        )
        collected_chunks = []
        collected_messages = []

        tmpchunk = ""
        redis =  get_sync_redis()

        for chunk in response:

            # print(chunk)
            if chunk:
                sid =  redis.get(f"socket:{sender}")
                if chunk['choices'][0]['delta']['content'] is not None:
                    chunk_message = chunk['choices'][0]['delta']['content']
                    collected_chunks.append(chunk_message)

                    if sid:
                        if tmpchunk:
                            data = await sio.emit("text_stream", {'r': tmpchunk + chunk_message, 'id': reply_id,
                                                                  'channel_id': channel_id}, sid)
                            # print(data)
                            tmpchunk = ""
                        else:
                            await sio.emit("text_stream",
                                           {'r': chunk_message, 'id': reply_id, 'channel_id': channel_id}, sid)
                    else:
                        tmpchunk = tmpchunk + chunk_message

                else:
                    print("stop")


        doc = {
            "uid":sender,
            "messages":messages
        }
        redis.lpush("dialog_quenen",json.dumps(doc))
        return ''.join(collected_chunks)



    @classmethod
    async def get_emotion(cls,msg:str):
        pass

