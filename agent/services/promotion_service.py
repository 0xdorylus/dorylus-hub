
import base58
import hashlib

import agent.utils.config as config


from agent.models.user import User
from agent.models.user_asset import UserAsset
from agent.models.user_promotion_log import UserPromotionLog
from agent.models.user_stat import UserStat
from agent.models.wish import WishRound, WishPool, WishTicket

from decimal import Decimal
class PromotionService:
    pass

    @classmethod
    async def wish_user_be_agent(cls,uid):
        user = await UserStat.get(uid)
        if user  and user.pid:
            await UserStat.find_one(UserStat.uid == uid).update({"$set":{"active":1}})
        else:
            pass
        desc = "升级到二级"
        op_type = "upgrade"
        mainchain = "BSC"
        token = "SCORE"
        amount = 300
        ticket_num = 6
        ticket_token = "TICKET"
        #自己
        await UserAsset.incr(uid,mainchain,token,Decimal(amount),op_type,desc)

        await UserAsset.incr(uid,mainchain,ticket_token,Decimal(ticket_num),op_type,desc)
        round = await WishRound.get_round()
        pool = await WishPool.get_pool( round)

        #添加到池子里面
        await WishTicket.add_ticket(uid,round,ticket_num,"bless",pool.id,token)

        await UserPromotionLog.recoard(uid,op_type,desc)
        # and user.level <= 0
        if user.pid :
            desc = "下线成为代理"
            op_type = "split_reward"
            amount = 100
            #注册上线直推
            await UserAsset.incr(user.pid,mainchain,token,amount,op_type,desc)
            msg = "注册上线直推,100奖励"
            await UserPromotionLog.recoard(uid, op_type, msg)

            items = await UserStat.get_active_child_list(user.pid)
            if len(items)>=2:
                active_pid = await UserStat.get_active_parent(user.pid)
                for child_user in items:
                    await UserStat.set_split_parent(active_pid,child_user.uid)
                msg = "下线转让"
                await UserPromotionLog.recoard(active_pid, op_type, msg)

        if user.split_pid:
            split_pid = user.split_pid
            #裂变直推
            split_user = await User.get(split_pid)
            level = split_user.level
            if level == 1:
                amount = 600
                await UserAsset.incr(split_user.uid, mainchain, token, amount, op_type, desc)
                await UserAsset.incr(split_user.uid, mainchain, ticket_token, ticket_num, op_type, desc)
                # 添加到池子里面
                await WishTicket.add_ticket(uid, round, ticket_num, "promotion", pool.id, token)

                msg = "获得600积分,6张许愿券"
                await UserPromotionLog.recoard(split_user.uid, op_type, msg)
            elif level == 2:
                amount = 300
                await UserAsset.incr(split_user.uid.pid, mainchain, token, amount, op_type, desc)
                await UserAsset.incr(split_user.uid, mainchain, ticket_token, ticket_num, op_type, desc)
                # 添加到池子里面
                await WishTicket.add_ticket(uid, round, ticket_num, "promotion", pool.id, token)

                msg = "获得300积分,6张许愿券"
                await UserPromotionLog.recoard(split_user.uid, op_type, msg)



