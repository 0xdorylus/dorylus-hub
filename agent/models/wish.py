import logging
import random

from beanie.odm.operators.update.array import AddToSet
from bson import ObjectId, Decimal128
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from ipaddress import IPv4Address
from decimal import Decimal

import pymongo
from beanie import Document, Indexed, before_event, after_event
import secrets
from beanie import Document, PydanticObjectId
from beanie import Insert

from agent.models.request_response_model import UserInfoModel
from agent.models.user import User
from agent.utils.common import get_unique_id

from eth_account import Account

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class WishCommentRequest(BaseModel):
    wish_id: str
    content: str


class WishReplyCommentRequest(BaseModel):
    comment_id: str
    content: str


class WishCommentListRequest(BaseModel):
    wish_id: str
    page: int
    pagesize: int = 100


class WishCommentListItem(BaseModel):
    id: str
    uid: str
    content: str
    wish_id: str
    wish_owner_id: str
    type: str
    create_at: datetime = datetime.now()
    creator: UserInfoModel = {}
    replys: List = []


class WishCommentListResponseModel(BaseModel):
    total: int = 0
    total_page: int = 0
    list: List[WishCommentListItem] = []


class ReplyModel(BaseModel):
    id: str
    creator: UserInfoModel = {}
    reply_user: UserInfoModel = {}
    content: str
    create_at: datetime


class WishComment(Document):
    id: str = Field(default_factory=get_unique_id)
    uid: str
    content: str
    wish_id: str
    wish_owner_id: str
    comment_id: str = ""
    comment_owner_id: str = ""
    type: str
    create_at: datetime = datetime.now()

    class Settings:
        name = "wish_comment"
        indexes = [
            [
                ("uid", pymongo.ASCENDING)
            ],
        ]

    @classmethod
    async def get_replys(cls, comment_id):
        print("comment_id:", comment_id)
        items = await cls.find({"comment_id": comment_id, "type": "reply"}).to_list()
        outs: List[ReplyModel] = []
        if items:
            for item in items:
                o = ReplyModel(**item.model_dump())
                o.creator = await  User.get_info(item.uid)
                o.reply_user = await  User.get_info(item.comment_owner_id)

                outs.append(o)

            return outs
        else:
            return []

    @classmethod
    async def del_comment(cls, uid, comment_id):
        await cls.find({"$and": [
            {"_id": comment_id},
            {
                "$or": [
                    {"uid": uid},
                    {"wish_owner_id": uid}
                ]
            }
        ]
        }).delete()

    @classmethod
    async def reply(cls, uid, comment_id, content):
        """
        回复评论


        """
        comment = await cls.get(comment_id)
        if comment:
            if comment.type == "comment":
                pass
            else:
                comment_id = comment.comment_id
            doc = {
                "uid": uid,
                "content": content,
                "comment_id": comment_id,
                'comment_owner_id': comment.uid,
                "wish_id": comment.wish_id,
                "wish_owner_id": comment.wish_owner_id,
                "type": "reply"
            }
            await cls(**doc).create()
        else:
            print("not found")

    @classmethod
    async def comment(cls, uid, wish_id, content):
        print(uid, wish_id, content)
        wish = await Wish.get(wish_id)
        if not wish.can_comment:
            print(wish)
            print("can't comment")
            return False
        doc = {
            "uid": uid,
            "content": content,
            "wish_id": wish_id,
            "wish_owner_id": await Wish.get_owner(wish_id),
            "type": "comment"
        }
        r = await cls(**doc).create()
        print(r)
        await Wish.inc_comment(wish_id)
        return True


class WishRequestModel(BaseModel):
    token: str
    content: str
    num: int
    can_comment: bool = True
    hide_self: bool = False


class WishHomeRequestModel(BaseModel):
    page: int = 1
    pagesize: int = 100
    sort: str = ""


class WishListItem(BaseModel):
    page: int = 1
    last_message_id: str = ""


class WishListItem(BaseModel):
    id: str
    uid: str
    token: str
    content: str
    num: float
    ticket_count: int
    can_comment: bool = True
    hide_self: bool = False
    comment_count: int = 0
    bless_count: int = 0
    share_count: int = 0
    creator: UserInfoModel = {}
    create_at: datetime


class WishDetail(BaseModel):
    id: str = Field(default_factory=get_unique_id)
    uid: str
    token: str
    content: str
    num: float
    round: int
    ticket_count: int
    can_comment: bool = True
    hide_self: bool = False
    comment_count: int = 0
    bless_count: int = 0
    share_count: int = 0
    can_admin:bool=False
    creator: UserInfoModel = {}
    create_at: datetime = datetime.now()


class WishListResponseModel(BaseModel):
    total: int = 1
    total_page: int = 1
    list: List[WishListItem] = []


class Wish(Document):
    id: str = Field(default_factory=get_unique_id)
    uid: str
    token: str
    content: str
    num: float
    round: int
    ticket_count: int
    can_comment: bool = True
    hide_self: bool = False
    comment_count: int = 0
    bless_count: int = 0
    share_count: int = 0

    create_at: datetime = datetime.now()
    update_at: datetime = datetime.now()

    class Settings:
        name = "wish"
        indexes = [
            [
                ("uid", pymongo.ASCENDING)
            ],
        ]

    @classmethod
    async def del_wish(cls,uid,id):
        await cls.find_one({"_id":id,"uid":uid}).delete()

    @classmethod
    async def get_owner(cls, id):
        vo = await cls.get(id)
        return vo.uid

    @classmethod
    async def like(cls, wish_id: str):
        await cls.find(cls.id == wish_id).inc({cls.bless_count: 1})

    @classmethod
    async def inc_comment(cls, wish_id: str):
        await cls.find(cls.id == wish_id).inc({cls.comment_count: 1})


class WishRound(Document):
    id: str = Field(default_factory=get_unique_id)
    round: Indexed(int, unique=True)

    @classmethod
    async def get_round(cls):
        item = await cls.find_one()
        if item:
            return item.round
        else:
            doc = {
                "round": 1
            }
            await cls(**doc).create()
            return 1

    @classmethod
    async def incr_round(cls):
        await cls.find_one().update({"$inc": {"round": 1}})

    class Settings:
        name = "wish_round"


class RedpktListItem(BaseModel):
    id: str
    token: str
    round: int
    current_num: int
    max_num: int
    status: str
    pool_user: List = [str]
    prize_list: List[int]


class RedpktListResponseModel(BaseModel):
    page: int
    total_page: int
    list: List[RedpktListItem]


class WishTicketListItem(BaseModel):
    id: str
    uid: str
    round: int
    status: str
    token: str
    pool_id: str
    prize: float = 0
    opened: bool
    creator: UserInfoModel = {}


class WishTicket(Document):
    id: str = Field(default_factory=get_unique_id)
    uid: str
    round: int
    token: str
    src: str = "bless"
    pool_id: str
    status: str = "pending"
    prize: float = 0
    opened: bool = False
    create_at: datetime = datetime.now()
    update_at: datetime = datetime.now()

    class Settings:
        name = "wish_ticket"




    @classmethod
    async def get_round_ticket_stat(cls,round,uid):
        unopened_num = await cls.find({"round":round,"uid":uid,"opened":False}).count()
        hit_num = await cls.find({"round":round,"uid":uid,"status":"hit","opened":True}).count()
        total_num = await cls.find({"round":round,"uid":uid}).count()

        return {
            "unopend_num":unopened_num,
            "hit_num":hit_num,
            "total_num":total_num
        }


    @classmethod
    async def get_unopened_ticket_num(cls,round,uid):
        num = await cls.find({"round":round,"uid":uid,"opened":False}).count()
        return num

    @classmethod
    async def open_redpkt(cls,round,uid):
        filter = {
            "uid":uid,
            "round":round,
            "status":"hit"
        }
        r = await cls.find_one(filter).update({"$set":{"opened":True}})
        if r.modified_count > 0:
            return True
        else:
            return False

    @classmethod
    async def generate_lucky(cls, wish_round, pool):
        logging.info("generate_lucky begin")

        items = await cls.find({"round": wish_round}).to_list()
        random.shuffle(items)
        max_len = len(items)
        if max_len > 10:
            select_items = random.sample(items, 10)
            max_len = 10
        else:
            select_items = random.sample(items, max_len)
        prize_list = [400, 40, 20, 10, 5, 5, 5, 5, 5, 5]
        logging.info("max_len: %d", max_len)
        hit_ticket_list:List[dict]=[]
        for i in range(0, max_len):

            prize = prize_list[i]
            ticket_id = select_items[i].id
            # print(ticket_id)
            # logging.info("ticket_id:",ticket_id)
            # logging.info(f"prize:%d",prize)
            await cls.find({"_id": ticket_id}).update({"$set": {"prize": prize, "status": "hit"}})
            hit = {
                "uid":select_items[i].uid,
                "ticket_id":ticket_id,
                "prize":prize,
                "opened":False
            }
            hit_ticket_list.append(hit)
        pool.hit_ticket_list = hit_ticket_list
        pool.status = "done"
        await  pool.save()

        await cls.find({"round": wish_round,"status":{"$ne":"hit"}}).update_many({"$set": {"status": "done"}})
        logging.info("generate_lucky done")

    #
    # @classmethod
    # async def open_ticket(cls,ticket_id,pool_id):
    #     r = await WishPool.find_one({"_id":pool_id,"current_num":{"$lt":10}}).update({"$inc":{"current_num":1}})
    #     if r.modified_num > 0:
    #         pass
    #         pool = await WishPool.get(pool_id)
    #         ticket_num = pool.ticket_num
    #
    #
    #     else:
    #         cls.set_done(ticket_id)
    #         return False
    @classmethod
    async def set_opened(cls, id):
        await cls.find_one(cls.id == id).update({"$set": {"opened": True}})

    @classmethod
    async def add_ticket(cls, uid, round, ticket_num, src, pool_id, token, add_ticket_num=False):
        for i in range(0, ticket_num):
            doc = {
                "uid": uid,
                "round": round,
                "token": token,
                "src": src,
                "pool_id": pool_id
            }
            await cls(**doc).create()
        if add_ticket_num:
            await WishPool.find_one({"round": round}).update({
                "$inc": {"ticket_num": ticket_num},
                "$addToSet": {"pool_user": uid}
            })


class WishRedpkt(Document):
    id: str = Field(default_factory=get_unique_id)
    token: str
    round: int
    prize_list: List[int]
    current_num: int = 0
    max_num: int = 10
    status: str = "pending"
    hit_user: List[str] = []
    pool_user: List[str] = [],

    class Settings:
        name = "wish_redpkt"


class WishPoolListItem(BaseModel):
    id: str
    ticket_num: int
    wish_num: int
    round: int
    status: str
    token: str
    my_total_ticket_num:int=0
    my_hit_ticket_num:int=0
    my_unopened_ticket_num:int=0
    hit_ticket_list:List=[]
    create_at:datetime


class WishPoolListResponseModel(BaseModel):
    total: int = 0
    total_page: int = 1
    list: List[WishPoolListItem] = []


class WishTicketListResponseModel(BaseModel):
    total: int = 0
    total_page: int = 1
    list: List[WishTicketListItem] = []


class WishPoolDetail(BaseModel):
    id: str
    ticket_num: int
    wish_num: int
    round: int
    status: str
    token: str
    open_process:int=0


class WishTicketHit(BaseModel):
    id:str
    uid:str
    ticket_id:str
    prize: float

class WishPoolItemDetail(BaseModel):
    id: str
    ticket_num: int
    wish_num: int
    round: int
    status: str
    token: str
    hit_ticket_list:List[WishTicketHit]=[]
class WishPoolListResponsModel(BaseModel):
    total:int=0
    total_page:int = 0
    list: List[WishPoolItemDetail] = []


class WishPool(Document):
    id: str = Field(default_factory=get_unique_id)
    ticket_num: int
    wish_num: int
    round: int
    status: str
    token: str
    pool_user: List[str] = [],
    hit_ticket_list: List[dict] = [],
    create_at: datetime = datetime.now()
    update_at: datetime = datetime.now()

    @classmethod
    async def get_pool(cls,round):
        pool = await cls.find_one({"round": round})
        if not pool:
            await cls.init_pool(round)
            pool = await cls.find_one({"round": round})
        return pool

    @classmethod
    async def init_pool(cls,round):
        token="WISH"
        doc = {
            "wish_num": 0,
            "ticket_num": 0,
            "round": round,
            "status": "prepare",
            "token": token,
            "pool_user": [],
            "hit_ticket_list": []
        }
        await WishPool(**doc).create()

    @classmethod
    async def add_ticket(cls, uid: str, token: str, wish_num: int, ticket_num: int):
        logger.info(f"add_ticket ,{uid},{token},{wish_num},{ticket_num}")

        wish_round = await WishRound.get_round()
        print("wish_round",wish_round)
        pool = await cls.find_one({"round": wish_round})
        print(pool)
        if not pool:
            doc = {
                "wish_num": wish_num,
                "ticket_num": ticket_num,
                "round": wish_round,
                "status": "prepare",
                "token": token,
                "pool_user": [uid],
                "hit_ticket_list": []
            }
            s = await WishPool(**doc).create()
            print(s)
        else:
            await cls.find_one({"round": wish_round}).update({
                "$inc": {"wish_num": wish_num, "ticket_num": ticket_num},
                "$addToSet": {"pool_user": uid}})

        pool = await cls.find_one({"round": wish_round})
        await WishTicket.add_ticket(uid, wish_round, ticket_num, "bless", pool.id, token)

        if pool.wish_num >= 1000:
            logging.info("begin to generate lucky babies")
            # 当前奖池关闭吧
            await cls.find_one({"round": wish_round}).update({"$set": {"status": "done", "update_at": datetime.now()}})
            # 增加轮次
            await WishRound.incr_round()
            await WishTicket.generate_lucky(wish_round, pool)

    class Settings:
        name = "wish_pool"
