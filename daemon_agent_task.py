
# This is a sample Python script.
import asyncio
import json
from datetime import datetime
import signal


import logging

from dotenv import load_dotenv

from agent.models.user import User
from agent.utils.redishelper import get_redis

# 加载.env文件
load_dotenv()

from agent.database import init_db


class UserFollowTask:

    def __int__(self):
        pass
    async def check_expire(self):

        redis = await get_redis()

        while True:

            item = await redis.rpop("user_follow_notice")
            if item is not None and item != "":
                data = json.loads(item)
                user = User(**data)
                id = user.id



            await asyncio.sleep(1)


async def main():
    # tid = await DBService.get_next("user_deposit_list")
    # print(tid)

    await init_db()
    executor = UserFollowTask()

    # asyncio.create_task(scanner.fetch_price()),
    #
    # await scanner.scan_block(34439531)
    # return
    tasks = [
        # asyncio.create_task(scanner.fetch_price()),
        asyncio.create_task(executor.check_expire()),

    ]
    await asyncio.gather(*tasks)

    def signal_handler(sig, frame):
        loop = asyncio.get_event_loop()
        tasks = asyncio.all_tasks(loop=loop)
        for task in tasks:
            print("task:", task)
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
