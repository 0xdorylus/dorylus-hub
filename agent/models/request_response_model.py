from datetime import datetime
from typing import List, Optional, Set, TypeVar

from pydantic import BaseModel, constr, Field

from agent.models.system_tag import SystemtTagModel

DataT = TypeVar("DataT")

class GeneralRequestModel(BaseModel):
    page: int = 1
    pagesize: int = 100
    uid:int=0
class MessageModel(BaseModel):
    kind: str = Field("", min_length=1, max_length=32)
    content: str = Field("", min_length=0, max_length=2048)
    receiver: str = Field("", min_length=0, max_length=100)
    channel_id: str = Field("", min_length=0, max_length=100)

class CreateAgentModel(BaseModel):
    nickname: str=""
    username:str= Field(min_length=3, max_length=40)
    avatar: str
    intro: str=""
    user_prompt:str=""
    greeting:str=""
    main_model:str="Lama3-8B"
    free_talk_num:int=1000
    visiablity:int=1
    user_tags: List[str]= []
    tag_ids: List[str]= []
    class Config:
        populate_by_name = True
        json_schema_extra = {
            'example': {
                'name': "role001",
                'avatar': 'https://s.0xbot.org/athena/01HA2BP40AYFB556WVGRDV8C2W/651b8500a8f9c1696302336.png',
                'user_tags': ['John'],
                'intro':"demo role",
                'tag_ids':['1111']
            }
        }


class HotModel(BaseModel):
    """
        热辣
    """
    hot: str = ""


class WishAssetModel(BaseModel):
    WISH: float = 0
    SCORE: int = 0
    TICKET: int = 0


class PromotionStatModel(BaseModel):
    level: int
    assets: WishAssetModel


class UniResponse(BaseModel):
    code: int = 0
    message: str = ""
    result: DataT


class ImageMessage(BaseModel):
    pass


class CaptchaMode(BaseModel):
    code: str


class UploadResponseModel(BaseModel):
    id: str = ""
    url: str = ""
    size: int = 0
    filename:str=""
    content_type:str=""


class UserInfoModel(BaseModel):
    id: str
    username: str = ""
    intro: str = ""
    avatar: str = ""
    verified: bool = False
    nickname: str = ""
    user_type:str=""


class UserInfoWithEmailModel(BaseModel):
    id: str
    username: str = ""
    avatar: str = ""
    email: str = ""
    verified: bool = False


class IDModel(BaseModel):
    id: str


class PoolRoundModel(BaseModel):
    round: int
    page: int = 0
    pagesize: int = 100


class SearchModel(BaseModel):
    q: str
    type: str = ""


class JoinGroupRequestModel(BaseModel):
    id: str
    memo: str = ""


class InviteModel(BaseModel):
    refcode: str


class AuthResponseModel(BaseModel):
    uid: str
    pid: str
    token: str
    username: str
    avatar: str
    invite_code: str
    invite_link: str
    jwt_token: str
    verified: bool = False


class BizAuthResponseModel(BaseModel):
    uid: str
    token: str
    username: str = ""
    avatar: str = ""
    acl: List[str] = []


class NonceResponseModel(BaseModel):
    nonce: str

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {"nonce": "this_is_unique_str_to_avoid_replay_attack"}
        }


class FinishResponseModel(BaseModel):
    """
        通用操作返回
    """
    code: int = 0
    message: str = Field("done", description="操作消息")

    class Config:
        populate_by_name = True
        json_schema_extra = {"example": {"message": "done"}}


class CreateAssistantResponseModel(BaseModel):
    id: str
    name: str
    avatar: str = ""
    # description: Optional[str] = ""
    intro: str = ""
    user_tags: List[str] = []
    tag_ids: List[str] = []

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "id": "str",
                "name": "str",
                "avatar": "str",
                "greeting": "str",
                "language": "str",
                "temperature": "float",
                "visiablity": "int",
                "free_talk_num": "int",
                "prompt": "str",
                "system_prompt": "str",
                "background": "str",
                "intro": "str",
                "main_model": "str",
                "user_tags": "List",
                "tag_ids": "List",
            }
        }


class FilterTagResponseModel(BaseModel):
    category: Set[str]
    items: List[SystemtTagModel]

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "category": ["Language", "Category"],
            "items": [
                {
                    "id": "01HC59ZXQYHZH81VK2HY83ZF91",
                    "title": "DeFI",
                    "value": "DeFI",
                    "tag": "Category",
                },
                {
                    "id": "01HC5A0G231PSJCB034DQT34MR",
                    "title": "NFT",
                    "value": "NFT",
                    "tag": "Category",
                },
                {
                    "id": "01HC5A100A7XJQSSA30NCYJTFJ",
                    "title": "English",
                    "value": "English",
                    "tag": "Language",
                },
            ],
        }


class AssistantListItemModel(BaseModel):
    id: str
    uid: str = ""
    name: str
    avatar: str = ""
    greeting: str = ""
    intro: str = ""
    creator: UserInfoModel = {}
    user_tags: List[str] = []
    tag_ids: List[str] = []
    chat_num: int = 0
    share_num: int = 0
    share_link: str = ""
    subscribed_num: int = 0


class GirlListItemItemModel(BaseModel):
    id: str
    name: str
    avatar: str
    mbti_type: str
    age: int
    race: str = ""
    personality: str = ""
    school: str = ""
    major: str = ""
    hometown: str = ""
    height: str = ""
    horoscope_sign: str = ""
    communication_style: str = ""
    outfit_style: str = ""
    hobbies: str = ""
    occupation: str = ""
    languages_spoken: str = ""
    social_media_intro: str = ""
    background: str = ""
    is_lock: bool = True


class GirlListResponseModel(BaseModel):
    total: int = 0
    total_page: int = 1
    list: List[GirlListItemItemModel] = []


class AssistantListResponseModel(BaseModel):
    total: int = 0
    total_page: int = 1
    list: List[AssistantListItemModel] = []


class AssistantListRequestModel(BaseModel):
    page: int = 1
    pagesize: int = 10
    tag_ids: List[str] = []

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "total": 1,
            "total_page": 1,
            "list": [
                {
                    "id": "01HD6BNY43CZHM9BYV63K1KTQH",
                    "uid": "01HC1ZZ65YK2X0FQ9R1620V4QB",
                    "name": "beeefff",
                    "avatar": "str",
                    "greeting": "str",
                    "creator": {
                        "uid": "01HC1ZZ65YK2X0FQ9R1620V4QB",
                        "avtar": "",
                        "username": "0xc6e8dbbf0170f430fbf8f2abb9097fd47457709d",
                        "user_type": 1,
                    },
                    "user_tags": ["joy"],
                    "tag_ids": [],
                    "chat_num": 0,
                    "share_num": 0,
                    "subscribed_num": 0,
                }
            ],
        }


class UserDetailModel(UserInfoModel):
    nickname: str = ""
    intro: str = ""
    pid: str = ""
    level: int = 0
    invite_num: int = 0
    user_type:str=""
    offical_verified: bool = False


class DeviceIdLoginModel(BaseModel):
    device_id: constr(strip_whitespace=True, min_length=10)
    refcode: str = ""


class PageRequestModel(BaseModel):
    page: int = 1
    pagesize: int = 100


class WishPageRequestModel(BaseModel):
    page: int = 1
    pagesize: int = 100
    status: str = ""
    round: int = 0


class AssetPageRequestModel(BaseModel):
    page: int = 1
    pagesize: int = 100
    op: str = ""
    token: str = ""


from decimal import Decimal, ROUND_HALF_UP


class AssetListItemModel(BaseModel):
    token: str = ""
    amount: Decimal = Field(..., decimal_places=8, rounding=ROUND_HALF_UP)

    op_type: str = ""
    desc: str = ""
    create_at: datetime


class AssetListResponseModel(BaseModel):
    total: int = 0
    total_page: int = 1
    list: List[AssetListItemModel] = []


class HistoryPageRequestModel(BaseModel):
    channel_id: str
    last_message_id: str


class PromptListItemModel(BaseModel):
    name: str
    prompt: str
    tag: str = ""
    model: str = ""
    description: str = ""
    icon: str = ""
    org: str = "openai"


class PromptListResponseModel(BaseModel):
    total: int = 0
    total_page: int = 1
    list: List[PromptListItemModel] = []


class CreateGroupModel(BaseModel):
    name: str
    intro: str
    logo: str = ""
    who_can_join:str="anyone"
    user_ids: List[str] = []
    type: str = "text_channel"
    category: str = ""
    create_agent: bool = False


class UpdateGroupModel(BaseModel):
    id: str
    name: str = ""
    intro: str = ""
    logo: str = ""
    category: str = ""
    banner: str = ""


class GroupInfoModel(BaseModel):
    id: str
    name: str
    intro: str
    logo: str = ""
    creator: UserInfoModel = {}
    type: str = "text_channel"
    category: str = ""


class GroupDetailModel(BaseModel):
    id: str
    name: str
    intro: str
    logo: str = ""
    user_ids: List[str] = []
    assistant_ids: List[str] = []
    admin_ids: List[str] = []
    creator: UserInfoModel = {}
    type: str = "text_channel"
    category: str = ""
    create_agent: bool = True


class ChannelListModel(BaseModel):
    id: str
    name: str
    intro: str
    logo: str = ""
    user_ids: List[str] = []
    type: str = "text_channel"
    category: str = ""


class ChannelUserListResponseModel(BaseModel):
    list: List[UserInfoModel] = []
    total: int = 0
    total_page: int = 1


class GroupListRequestModel(BaseModel):
    page: int = 1
    pagesize: int = 10


class GroupListResponseModel(BaseModel):
    page: int = 1
    total_page: int = 10
    list: List[GroupDetailModel] = []
