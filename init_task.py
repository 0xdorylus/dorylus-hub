# This is a sample Python script.
import asyncio
from datetime import datetime
import signal
import sys
import threading

import aiohttp
import requests
from fastapi import FastAPI
from pymongo.errors import DuplicateKeyError
# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.

from web3 import Web3, AsyncWeb3
import os
import time
from beanie import init_beanie, Document
from motor.motor_asyncio import AsyncIOMotorClient
import binascii

from web3.middleware import geth_poa_middleware

from app.models.request_response_model import CreateAgentModel
from app.models.stake import Stake
from app.models.task import TaskBox
from app.models.user import User, LoginWithSignModel
from app.models.system_tag import   SystemTag

from app.models.user_stat import UserStat
from app.models.user_asset import UserAsset
from app.models.file_meta import FileMetadata
from app.models.assistant import Assistant
from app.models.op_log import OpLog
from app.models.subscribe import Subscription
from app.models.article import Article,ArticleCategory

# from app.models.file_meta import FileMetadata,SoldityFileMeta
# from app.models.solidity import DeployedContract
from app.models.biz_user import BizUser, BizUserModel
from app.models.channel import Channel
from app.models.chat_message import ChatMessage
from app.models.system_prompt import SystemPrompt
from app.models.friend_request import FriendRequest
from app.models.feedback import Feedback

from app.models.user_acheievements import Achievement,UserAchievement
from app.models.user_social import UserSocial
from app.models.knowledge import Knowledge, KnowledgeFileRecord
from app.models.conversation import Conversation
from app.models.user_asset import UserAsset
from app.models.user_wallet import UserWallet
from app.models.pay_product import PayProduct
from app.models.apple_order import AppleOrder
from app.models.user_promotion_log import UserPromotionLog
from app.models.user_asset_list import UserAssetList
from app.models.token_gate import TokenGate
from app.models.acl import Acl
from app.models.friend_request import JoinGroupRequest
from app.models.wish import WishPool,WishTicket,WishRound,Wish,WishComment
from app.models.user_config import UserConfig
from app.models.chat_message import ChatMessage,ChatGroupMessage,ChatGroupUserMessagePosition,ChatDialogMessage
from app.models.contact import Contact
from app.models.paybox import PayOrder
from app.models.luck import LotteryUser,Lottery
from app.models.counter import Counter
from app.models.user_login import UserLogin
from app.models.topic import Topic
from app.models.notice import Notice
from app.models.user_deposit_list import UserDepositList
from app.models.stake_list import StakeList
from app.models.user_asset import UserCollectList,UserWithdraw
from app.models.coin_price import CoinPrice
from app.models.check_hash_task import CheckHashTask
from app.models.user_invest import UserInvest
from app.models.agent import Agent
import logging

from dotenv import load_dotenv
from decimal import Decimal

from app.services.agent_service import AgentService
from app.services.user_service import UserService
from app.database import init_db


from app.utils.common import logger
# 加载.env文件
load_dotenv()

# 读取变量
db_name = os.getenv("DB_NAME")
if not db_name:
    print("lack DB_NAME enviroment variable")
    sys.exit(1)





async def init():
    logger.info("init db start")
    # Create Motor client
    await init_db()
    logger.info("init db done")






class DBExecutor(object):






    async def init_task(self):
        system_channel_id = os.getenv("SYSTEM_CHANNEL_ID")
        system_address = os.getenv("SYSTEM_ADDRESS")

        system_address = system_address.lower()
        user = await User.by_address(system_address)
        if user is None:
            return
        # channel = await Channel.get_channel(user.id,)
        task = await TaskBox.get_onboarding_task(system_channel_id)
        if not task:
            doc = {
                "target": system_channel_id,
                "task_type":"onboard",
                "creator": user.id,
                "tag":"channel",
                "name": "User Onboarding",
            }
            await TaskBox.create(**doc)






# Set the signal handler

async def main():
    await init()
    scanner = DBExecutor()
    tasks = [
        asyncio.create_task(scanner.init_task()),


    ]
    await asyncio.gather(*tasks)



    def signal_handler(sig, frame):
        loop = asyncio.get_event_loop()
        tasks = asyncio.all_tasks(loop=loop)
        for task in tasks:
            print("task:",task)
            task.cancel()
        loop.stop()


    signal.signal(signal.SIGINT, signal_handler)

# Press the green button in the gutter to run the script.

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("async io")
        pass

