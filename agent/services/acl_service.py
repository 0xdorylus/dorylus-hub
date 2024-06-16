from agent.constant import AssistantNumLimit, UserLevel
from agent.models.user import User
from agent.models.user_asset import UserAsset
from fastapi import FastAPI, HTTPException


class AclService:
    def __init__(self):
        pass

    @classmethod
    async def user_can_create_article(self, uid: str):
        return True

    async def user_can_list_feedback(self, uid: str):
        return True


    @classmethod
    async def user_can_create_agent(self, uid: str):
        user = await User.find_one(User.id==uid)
        if user is None:
            return False
        # if user.verified == False:
        #     raise HTTPException(status_code=403, detail="User not verified")
        # if user.level < 1:
        #     raise HTTPException(status_code=403, detail="User leve < 1")


        # #limit num
        # if user.level == UserLevel.NORMAL and user.assistant_count >= AssistantNumLimit.NORMAL_NUM:
        #     raise HTTPException(status_code=403, detail="NUM LIMIT")
        # if user.level == UserLevel.VIP and user.assistant_count >= AssistantNumLimit.VIP_NUM:
        #     return False



        return True
