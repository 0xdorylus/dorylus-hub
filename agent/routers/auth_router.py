import logging
from datetime import datetime

from fastapi import APIRouter

from agent.models.request_response_model import AuthResponseModel, NonceResponseModel, FinishResponseModel, \
    DeviceIdLoginModel
from agent.services.mail_service import MailService
from agent.utils.blockhelper import verify_signature
from agent.utils.common import success_return, get_unique_id, get_host, get_current_time
from agent.utils.redishelper import get_redis
from agent.models.base import GenericResponseModel
from agent.models.user import LoginWithSignModel, User, LoginWithEmailModel, LoginWithUsername, SignUpWithEmailModel, \
    VerifyEmailModel, UserInfoModel
from fastapi import APIRouter, HTTPException, Depends
from agent.utils.x_auth import get_uid_by_token

router = APIRouter()
from agent.services.user_service import UserService
from fastapi import Depends, Request

# from agent.models.auth import AccessToken, RefreshToken
from agent.utils.x_auth import api_key_header
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

oauth2_sceme = OAuth2PasswordBearer("/token")


# 生成token
@router.post("/auth/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), user_service: UserService = Depends()):
    # print(form_data.__dict__)
    # {'grant_type': 'password', 'username': 'jim', 'password': 'pwd', 'scopes': [], 'client_id': None,
    #  'client_secret': None}

    pass




    # token = gen_token(user.username)
    # user_dict["token"] = token

    # return {"access_token": token, "token_type": "bearer"}

#
@router.post("/auth/account/create_with_email",response_model=GenericResponseModel[UserInfoModel], tags=["auth"],summary="使用过email创建账号")
async def create_with_email(create_form: SignUpWithEmailModel, request: Request,
                            user_service: UserService = Depends()):
    client_host = request.headers.get("X-Forwarded-For")
    data =  await user_service.create_with_email(create_form.email, create_form.password, create_form.invite, client_host)
    return GenericResponseModel(result=data)


#
@router.post("/auth/account/verify_email",  response_model=GenericResponseModel,tags=["auth"],summary="验证emai地址(邀请登录)")
async def verify_email(vo: VerifyEmailModel, request: Request, uid: str = Depends(get_uid_by_token),
                       user_service: UserService = Depends()) :
    """
        测试的时候输入168168作为超级验证码

    """
    client_host = request.headers.get("X-Forwarded-For")
    ret = await user_service.verify_email(vo.email, vo.code)
    return GenericResponseModel()


#
@router.post("/auth/account/send_verify_email", response_model=GenericResponseModel,tags=["auth"],summary="发送email验证地址")
async def send_verify_email(uid: str = Depends(get_uid_by_token),
                            mail_service: MailService = Depends()) :
    await mail_service.send_verify_code(uid)
    return GenericResponseModel()


#
#
#
@router.post("/auth/login_with_email", response_model=GenericResponseModel[AuthResponseModel], tags=["auth"],summary="使用email登录")
async def login_with_email(form: LoginWithEmailModel, request: Request, user_service: UserService = Depends()):
    client_host = request.headers.get("X-Forwarded-For")

    data =  await user_service.login_with_email(form.email, form.password, form.captcha, client_host)
    return GenericResponseModel(result=data)





@router.post("/auth/loginwithsign", response_model=GenericResponseModel[AuthResponseModel], tags=["auth"],summary="签名登录")
async def loginwithsign(login_form: LoginWithSignModel,  request: Request,user_service: UserService = Depends()):
    """
       签名登录

       使用EVM兼容个方法进行签名登录，如果用户地址不存在，则注册新用户
       签名消息
    """

    address = login_form.address
    message = login_form.msg
    signature = login_form.sig
    flag = verify_signature(address, message, signature)
    if flag:
        user = await user_service.get_user_by_address(address)
        if user is None:
            user = await user_service.create_user_with_sign(login_form)
            if user is None:
                raise HTTPException(status_code=401, detail="crete user error")
            else:
                logging.info("create user with sign success")
                access_token = await user_service.create_access_token(user.id)
        else:
            access_token = await user_service.create_access_token(user.id)

        data = {
            "token": access_token,
            "uid": user.id,
            "username": user.username,
            'avatar': user.get_avatar(),
            "invite_code": user.invite_code,
            "invite_link": user.get_invite_link(),
            "jwt_token": access_token,
            "pid": user.pid,
            "verified": user.verified,
        }
        user.last_login_at=get_current_time()
        ip = get_host(request)
        user.last_login_ip=ip
        await  user.save()
        return GenericResponseModel(result=AuthResponseModel(**data))
    else:
        raise HTTPException(status_code=401, detail="Bad Signature")


@router.post("/auth/logout", response_model=GenericResponseModel,tags=["auth"],summary="退出登录")
async def logout(token: str = Depends(api_key_header), user_service: UserService = Depends()):
    if token:
        redis = await get_redis()
        uid = await redis.get(token)
        if uid:
            await user_service.logout(uid)
        else:
            logging.error("logout error,no uid")
    else:
        logging.error("logout error,no token")
    return GenericResponseModel()


@router.post("/auth/get_nonce", response_model=GenericResponseModel[NonceResponseModel],tags=["auth"],summary="获得随机数")
async def get_nonce():
    redis = await get_redis()
    nonce = get_unique_id()
    await redis.set(nonce, 1)
    data =  NonceResponseModel(**{"nonce":nonce})
    return GenericResponseModel(result=data)




@router.post("/auth/login_with_device_id", response_model=AuthResponseModel, tags=["auth"],summary="设备ID登录")
async def login_with_device_id(login_form: DeviceIdLoginModel,  request: Request,user_service: UserService = Depends()):
    """
       IOS设备登录

       IOS App生存唯一的设备号
    """
    device_id = login_form.device_id


    user = await user_service.get_user_by_device_id(device_id)
    if user is None:
        user = await user_service.create_user_with_device_id(login_form)
        if user is None:
            raise HTTPException(status_code=401, detail="Bad sign")
        else:
            logging.info("create user with sign success")
            access_token = await user_service.create_access_token(user.id)
    else:
        access_token = await user_service.create_access_token(user.id)

    data = {
        "token": access_token,
        "uid": user.id,
        "username": user.get_username(),
        'avatar': user.get_avatar(),
        "invite_code": user.invite_code,
        "invite_link": user.get_invite_link(),
        "jwt_token": access_token,
        "pid": user.pid,
        "verified": user.verified,
    }
    user.last_login_at = get_current_time()
    ip = get_host(request)

    user.last_login_ip=ip
    await  user.save()
    return AuthResponseModel(**data)

