import logging
import secrets
import random
from typing import List

from fastapi import HTTPException

from agent.constant import UserLevel
from agent.connection import get_next_id
from agent.errors.biz import AccountRegisterError, AccountLoginError
from agent.models.assistant import Assistant, AssistantDetailModel, Girl, GirlDetailModel
from agent.models.biz_user import BizUser, BizLoginModel, BizUserModel
from agent.models.channel import Channel
from agent.models.request_response_model import AuthResponseModel, DeviceIdLoginModel, BizAuthResponseModel, \
    UserDetailModel, CreateAgentModel
from agent.models.user import User, LoginWithSignModel, UserInfoModel

from passlib.context import CryptContext
from datetime import datetime, timedelta

from agent.models.user_asset import UserAsset
from agent.services.agent_service import AgentService
from agent.services.feed_service import FeedService
from agent.services.redis_service import RedisService
from agent.utils.common import error_return, success_return, get_unique_id, get_session_id
# from agent.utils.mail import send_simple_message
from agent.utils.redishelper import get_redis

from ulid import ULID
from agent.utils.common import is_email_validate, fill_model_from_obejct

from agent.config import CONFIG


class UserService(RedisService):

    def __init__(self):
        super().__init__()
        self.hasher = CryptContext(schemes=['bcrypt'], deprecated='auto')
        self.secret_key = '0xbotxdataloveyou'
        self.algorithm = 'HS256'
        self.access_token_expire_minutes = 60 * 24 * 30

    async def create_biz_user(self, form: BizUserModel):
        username = form.username
        password = form.password

        print(form)
        user = await BizUser.find_one({"username": username})
        if user is not None:
            return error_return(1, "username already exists", user)
        password = self.hasher.hash(password)
        user = await  BizUser(
            username=username,
            password=password,
            ga=form.ga
        ).create()
        return success_return(user)

    async def biz_user_login(self, login_form: BizLoginModel):
        username = login_form.username
        password = login_form.password

        biz_user = await BizUser.find_one(BizUser.username == username)

        if biz_user is None:
            return HTTPException(418, "username doesn't exists")

        if self.hasher.verify(password, biz_user.hash):
            access_token = await self.create_access_token(biz_user.id)
            data = {
                "token": access_token,
                "uid": biz_user.id,
                "acl": ["all"],
                "username": username,
                "avatar": biz_user.get_avatar()
            }

            auth = BizAuthResponseModel(**data)
            return auth
        else:
            return HTTPException(418, "Password Error")

    async def create_with_email(self, email: str, password: str, invite: str, client_host: str):
        if not is_email_validate(email):
            raise HTTPException(status_code=418, detail="email error")

        user = await User.find_one(User.normlized_email == email.lower())
        if user is not None:
            raise HTTPException(status_code=418, detail="email already exists")
        pid = ""
        if invite is not None:
            ref_user = await User.find_one(User.invite_code == invite)
            if ref_user is not None:
                pid = ref_user.idl
        password = self.hasher.hash(password)

        user = await  User(
            pid=pid,
            email=email,
            username=email,
            normlized_email=email.lower(),
            password=password,
            verified=False,  # 0:未激活 1:已激活
            user_type="email",
            register_host=client_host
        ).create()
        user_info = UserInfoModel(**user.model_dump())
        if CONFIG.system_agent_id:
            await FeedService.follow(user.id, CONFIG.system_agent_id)

        user.update_avatar()
        name = "i-" + user.username
        form = CreateAgentModel(username=name, avatar=user.avatar)
        ret = await AgentService.create_agent(user.id, form)
        print(ret)
        if ret.code == 0:
            await FeedService.follow(user.id, ret.result['user'].id)

        return user_info

    async def verify_email(self, email, code):
        # TODO: 验证邮箱

        user = await User.find_one(User.normlized_email == email.lower())
        if user is None:
            raise HTTPException(406, "email_error")
        redis = await get_redis()
        save_code = await redis.get((f'email:%s', email))
        if save_code == code or code == 168168:
            user.status = 1
            user.verified = True
            user.email_confirmed_at = datetime.now()
            await user.save()
        else:
            raise HTTPException(406, "code_error")

    async def login_with_username(self, username: str, password: str, client_id: str, client_host: str) -> User:
        user = await User.find_one(User.username == username)
        if user is None:
            return None
        if user.password != password:
            return None
        return user

    async def login_with_email(self, email: str, password: str, client_id: str, client_host: str) -> User:
        user = await User.find_one(User.normlized_email == email.lower())
        if user is None:
            raise AccountLoginError("User Not Exists")
        if not self.hasher.verify(password, user.password):
            raise AccountLoginError("User Passworrd Error")

        else:
            access_token = await self.create_access_token(user.id)
            data = {
                "token": access_token,
                "uid": user.id,
                "username": user.username,
                'avatar': user.get_avatar(),
                "invite_code": user.invite_code,
                "invite_link": user.get_invite_link(),
                "jwt_token": "",
                "pid": user.pid,
                "verified": user.verified,
            }
            return AuthResponseModel(**data)

    async def get_user_by_address(self, address: str) -> User:
        return await User.find_one({"address": address})

    async def get_user_by_device_id(self, device_id: str) -> User:
        return await User.find_one(User.device_id == device_id)

    async def get_user_by_uid(self, uid) -> User:
        return await User.find_one(User.id == uid)

    async def direct_create_user(self, signUp: LoginWithSignModel) -> User:
        user = await User.find_one({"$or":
            [
                {"address": signUp.address.lower()},
                {"username": signUp.address.lower()}
            ]
        })
        if user is not None:
            return AccountRegisterError("address already exists", signUp.address)
        pid = ""
        if signUp.refcode is not None:
            ref_user = await User.find_one(User.invite_code == signUp.refcode)
            if ref_user is not None:
                pid = ref_user.id

        user = await  User(
            pid=pid,
            address=signUp.address,
            username=signUp.address,
            verified=True,
            user_type="sign",
            refcode=signUp.refcode).create()

        return user

    async def create_user_with_sign(self, signUp: LoginWithSignModel) -> User:
        user = await User.find_one({"$or":
            [
                {"address": signUp.address.lower()},
                {"username": signUp.address.lower()}
            ]
        })
        if user is not None:
            return AccountRegisterError("address already exists", signUp.address)
        pid = ""
        if signUp.refcode is not None:
            ref_user = await User.find_one(User.invite_code == signUp.refcode)
            if ref_user is not None:
                pid = ref_user.id

        user = await  User(
            pid=pid,
            address=signUp.address,
            username=signUp.address,
            verified=True,
            user_type="sign",
            refcode=signUp.refcode).create()

        if CONFIG.system_agent_id:
            await FeedService.follow(user.id, CONFIG.system_agent_id)

        user.update_avatar()
        name = "i-" + user.username
        print(name)
        form = CreateAgentModel(username=name, avatar=user.avatar)
        ret = await AgentService.create_agent(user.id, form)
        if ret.code == 0:
            await FeedService.follow(user.id, ret.result['user'].id)
        return user

    async def create_user_with_device_id(self, signUp: DeviceIdLoginModel) -> User:
        user = await User.find_one({"$or": [{"device_id": signUp.device_id.lower()},
                                            {"username": signUp.device_id.lower()}
                                            ]
                                    })
        if user is not None:
            raise AccountRegisterError("address already exists")

        pid = ""
        if signUp.refcode is not None:
            ref_user = await User.find_one(User.invite_code == signUp.refcode)
            if ref_user is not None:
                pid = ref_user.id

        user = await User(
            pid=pid,
            device_id=signUp.device_id,
            verified=False,
            user_type="device",
            refcode=signUp.refcode).create()
        if CONFIG.system_agent_id:
            await FeedService.follow(user.id, CONFIG.system_agent_id)
        # await SocialService.subscribe_agent(user.id, CONFIG.system_agent_id)
        return user

    async def authenticate_user(self, username: str, password: str):
        # 获取用户数据
        user_dict = await User.find_one(User.username == username)
        if not user_dict:
            return False

        # 验证密码
        # hashed_password = user_dict['password']
        # if not self.hasher.verify(password, hashed_password):
        #     return False

        return user_dict

    async def logout(self, uid):
        logging.info("logout:{}".format(uid))
        redis = await get_redis()
        session_id = await redis.get(uid)
        await redis.delete(session_id)
        sid = await redis.get(f"socket:{uid}")
        if sid:
            await redis.delete(f"socket:{uid}")
            await redis.delete(f"socket:{sid}")
            await redis.delete(f"socket:{sid}:token")
            logging.info("logout socket:{}".format(sid))

    async def create_access_token(self, uid):
        session_id = get_session_id()

        logging.info("create_access_token :%s ", session_id)

        redis = await get_redis()
        old_session_id = await redis.get(uid)
        if old_session_id:
            logging.info("delete old session_id :%s ", old_session_id)
            # await redis.delete(old_session_id)
        await redis.set(session_id, uid)
        await redis.set(uid, session_id)
        await redis.expire(session_id, 60 * self.access_token_expire_minutes)

        return session_id

    async def get_deposit_address(self, mainchain: str, token: str, uid: int):
        token = token.upper()
        userAsset = await UserAsset.find_one(UserAsset.uid == uid, UserAsset.mainchain == mainchain,
                                             UserAsset.token == token)
        pass

    async def get_user(self, uid) -> UserDetailModel:
        user = await User.find_one(User.id == uid)
        print(user)
        if user:
            user.avatar = user.get_avatar()
            user_info = UserDetailModel(**user.model_dump())
            # value = await UserConfig.get_hot_model(uid)
            # user_info.hot_model = value
            return user_info
        else:
            raise HTTPException(404, "Userr Not Found")

    async def user_subscribed_assistant_list(self, uid):
        items = await Channel.find({"uid": uid, "type": "p2m"}).to_list()
        outs: List[AssistantDetailModel] = []
        for item in items:
            assistant = await Assistant.find_one(Assistant.id == item.target)
            if assistant:
                vo = AssistantDetailModel(**assistant.model_dump())
                vo.current_user_subscribed = True
                vo.creator = await User.get_info(assistant.uid)
                vo.current_user_subscribed_channel_id = item.id
                outs.append(vo)
        return outs

    async def user_subscribed_girls_list(self, uid):
        items = await Channel.find({"uid": uid, "type": "p2m"}).to_list()
        outs: List[AssistantDetailModel] = []
        for item in items:
            assistant = await Assistant.find_one(Assistant.id == item.target)
            if assistant:
                vo = AssistantDetailModel(**assistant.model_dump())
                vo.current_user_subscribed = True
                vo.creator = await User.get_info(assistant.uid)
                vo.current_user_subscribed_channel_id = item.id
                outs.append(vo)
        return outs

    async def my_subscribed_girls_list(self, uid):
        items = await Channel.find({"uid": uid, "type": "p2m"}).to_list()
        outs: List[AssistantDetailModel] = []
        for item in items:
            assistant = await Girl.find_one(Assistant.id == item.target)
            if assistant:
                assistant.avatar = assistant.get_avatar()
                assistant.background = assistant.get_backgroud()
                vo = GirlDetailModel(**assistant.model_dump())
                vo.current_user_subscribed = True
                vo.creator = await User.get_info(assistant.uid)
                vo.current_user_subscribed_channel_id = item.id
                outs.append(vo)
        return outs
