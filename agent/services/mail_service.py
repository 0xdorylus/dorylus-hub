import httpx
import requests
from fastapi import HTTPException

from agent.models.request_response_model import FinishResponseModel
from agent.models.user import User
from agent.utils.common import generate_random_string, success_return, error_return
from agent.utils.redishelper import get_redis

mail_key = ""
class MailService:
    def __init__(self):
        pass


    async def send_verify_code(self,uid):
        user = await  User.get(uid)
        if user:
            email  = user.email
            if email:
                code = generate_random_string(6)
                redis = await get_redis()
                await redis.setex((f'email:%s',email),code)
                return FinishResponseModel()
        else:
            raise HTTPException(418,"User Errror")




    async def send_simple_message(self,target_mail,code):
        async with httpx.AsyncClient() as aclient:
            aclient.post(
            "https://api.mailgun.net/v3/mail.dorylus.ai/messages",
            auth=("api", mail_key),
            data={"from": "dorylus-protocl <service@mail.dorylus.ai>",
                  "to": [target_mail],
                  "subject": "Welcome to join dorylus world",
                  "text": "Welcome to joindorylus-protocol world ,an AI and blockchain driven world.Your register code is: "+str(code)})

# r =  MailService().send_simple_message()
# print(r)