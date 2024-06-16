import json

from agent.models.chat_message import ChatMessage, ChatDialogMessage
from agent.models.system_prompt import SystemPrompt
from agent.services.redis_service import RedisService



from agent.utils.redishelper import get_redis

from agent.websocket.socket_manager import manager
from openai import AsyncOpenAI
from agent.config import CONFIG

client = AsyncOpenAI(
    # This is the default and can be omitted
    api_key=CONFIG.openai_key,
)

class LLMService:
    llm: None

    def __init__(self) -> None:
        # self.llm = OpenAI(temperature=0.9)
        pass




    # async def get_system_prompt(self):
    # llm = OpenAI(streaming=True, callbacks=[MyCustomHandler()], temperature=0)
    # resp = llm("Write me a song about sparkling water.")

    @classmethod
    async def send(self,channel_id, sender, agent_id, content, reply_id):

        messages = []

            # system_prompt 是对 AI 模型的角色定义和输出约束
            # history 是历史的对话信息，包括用户问题和AI回复
            # message 是当前用户提问的问题
        system_prompt = await SystemPrompt.get_system_prompt(agent_id)
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        history = await ChatDialogMessage.get_ai_history_pair(channel_id, sender)
        # print("history")
        # print(history)
        for item in history:
            # item[0] 是用户问题， item[1] 是AI回复
            messages.append({"role": "user", "content": item[0]})
            messages.append({"role": "assistant", "content": item[1]})

            # messages.append(AIMessage(content=item[1]))
        # 最后是当前用户问题
        messages.append({"role": "user", "content": content})

        stream = await client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=messages,
            stream=True,
        )
        collected_chunks = []
        async for chunk in stream:
            chunk_message = chunk.choices[0].delta.content or ""
            if chunk_message is not None and chunk_message != "":
                collected_chunks.append(chunk_message)
                msg = {
                    "kind":"stream",
                    "content":chunk_message,
                    "channel_id":channel_id,
                    "sender":sender,
                    "id":reply_id
                }
                await manager.send(sender,json.dumps(msg))

        return ''.join(collected_chunks)
