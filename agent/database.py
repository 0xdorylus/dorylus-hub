from beanie import init_beanie

import motor.motor_asyncio
from dotenv import load_dotenv

from agent.models.stake import Stake
from agent.models.user import User, LoginWithSignModel
from agent.models.system_tag import   SystemTag

from agent.models.user_stat import UserStat
from agent.models.user_asset import UserAsset
from agent.models.file_meta import FileMetadata
from agent.models.assistant import Assistant
from agent.models.op_log import OpLog
from agent.models.subscribe import Subscription
from agent.models.article import Article,ArticleCategory
from agent.models.notice import Notice

# from agent.models.file_meta import FileMetadata,SoldityFileMeta
# from agent.models.solidity import DeployedContract
from agent.models.biz_user import BizUser
from agent.models.channel import Channel,ChannelFile
from agent.models.chat_message import ChatMessage
from agent.models.system_prompt import SystemPrompt
from agent.models.friend_request import FriendRequest
from agent.models.feedback import Feedback

from agent.models.user_acheievements import Achievement,UserAchievement
from agent.models.user_social import UserSocial
from agent.models.knowledge import Knowledge, KnowledgeFileRecord
from agent.models.conversation import Conversation
from agent.models.user_asset import UserAsset
from agent.models.user_wallet import UserWallet
from agent.models.pay_product import PayProduct
from agent.models.apple_order import AppleOrder
from agent.models.user_promotion_log import UserPromotionLog
from agent.models.user_asset_list import UserAssetList
from agent.models.token_gate import TokenGate
from agent.models.acl import Acl
from agent.models.friend_request import JoinGroupRequest
from agent.models.wish import WishPool,WishTicket,WishRound,Wish,WishComment
from agent.models.user_config import UserConfig
from agent.models.chat_message import ChatMessage,ChatGroupMessage,ChatGroupUserMessagePosition,ChatDialogMessage
from agent.models.contact import Contact
from agent.models.paybox import PayOrder
from agent.models.luck import LotteryUser,Lottery
from agent.models.counter import Counter
from agent.models.user_login import UserLogin
from agent.models.topic import Topic
from agent.models.notice import Notice
from agent.models.user_deposit_list import UserDepositList
from agent.models.stake_list import StakeList
from agent.models.user_asset import UserCollectList,UserWithdraw
from agent.models.coin_price import CoinPrice
from agent.models.check_hash_task import CheckHashTask
from agent.models.user_invest import UserInvest
from agent.models.agent import Agent
from agent.models.user_social import UserFollow,UserDMSetting,UserFollowNotice,UserTweet
from agent.models.task import TaskBox,TaskItem,UserTaskBox,UserTaskItem
from agent.services.agent_service import AgentService
from agent.services.user_service import UserService

load_dotenv()
import os
from agent.connection import db
import sys

async def init_db():
    await init_beanie(database=db, document_models=[Notice,ChannelFile,UserFollow,UserDMSetting,UserFollowNotice,UserTweet,UserWithdraw,Agent,UserInvest, UserDepositList, UserCollectList, StakeList, Stake, BizUser, KnowledgeFileRecord, Knowledge, CoinPrice, CheckHashTask, UserDepositList, Notice, Topic, UserLogin, Counter, LotteryUser, Lottery, PayOrder, Contact, ChatDialogMessage, ChatMessage, ChatGroupMessage, ChatGroupUserMessagePosition, UserConfig, WishComment, WishPool, WishTicket, WishRound, Wish, JoinGroupRequest, Acl, TokenGate, UserAssetList, UserPromotionLog, AppleOrder, PayProduct, Achievement, UserAsset, UserWallet, KnowledgeFileRecord, Knowledge, Conversation, UserSocial, UserAchievement, Feedback, FriendRequest, Article, ArticleCategory, ChatMessage, SystemPrompt, Subscription, SystemTag, Channel, User, OpLog, UserStat, UserAsset, FileMetadata, Assistant])
    counter_collection = await db.counter.find_one({"type": "user"})
    if counter_collection is None:
        await db.create_collection("counter")
        await db.counter.insert_one({"type": "user", "seq": 0})





