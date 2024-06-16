"""
FastAPI server configuration
"""
from typing import List

# pylint: disable=too-few-public-methods

from decouple import config, Csv
from pydantic import BaseModel


class Settings(BaseModel):
    """Server config settings"""

    token_list: List[str] = config("ASSET_TOKENS", default=['USDT'], cast=Csv(str))
    deposit_token_list: List[str] = config("DEPOSIT_SUPPORRT_TOKENS", default=['USDT'], cast=Csv(str))


    mainchain:str=config("mainchain",default="BSC",cast=str)
    member_fee:int=config("mainchain",default=300,cast=int)
    invite_domain:str=config("INVITE_DOMAIN",default="",cast=str)
    default_user_avatar:str=config("DEFAULT_USER_AVATAR",default="",cast=str)
    default_channel_avatar:str=config("DEFAULT_CHANNEL_AVATAR",default="",cast=str)
    default_role_avatar:str=config("DEFAULT_ROLE_AVATAR",default="",cast=str)
    invite_join_group_link:str=config("INVITE_JOIN_GROUP_LINK",default="",cast=str)
    sio_redis_url:str=config("SIO_REDIS_URL",default="",cast=str)
    nabox_merchant_id:str=config("NABOX_MERCHANT_ID",default="",cast=str)
    openai_key:str=config("OPENAI_KEY",default="",cast=str)
    open_router_key:str=config("OPEN_ROUTER_KEY",default="",cast=str)
    use_open_router:str=config("USE_OPEN_ROUTER",default=False,cast=bool)
    db_save_key:str=config("DB_SAVE_KEY",default="",cast=str)
    private_key_path:str=config("PRIVATE_KEY_PATH",default="",cast=str)
    fs_store_dir:str=config("FS_STORE_PATH",default="",cast=str)
    file_domain:str=config("FILE_DOMAIN",default="",cast=str)

    system_agent_id:str=config("SYSTEM_AGENT_ID",default="",cast=str)
    app_key:str=config("APP_KEY",default="",cast=str)


CONFIG = Settings()
