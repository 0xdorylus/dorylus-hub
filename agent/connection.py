from beanie import init_beanie

import motor.motor_asyncio
import os

from dotenv import load_dotenv

load_dotenv()
db_name = os.getenv("DB_NAME")
db_connection = os.getenv("DB_CONNECTION")
# uri = "mongodb://user:pass@localhost:27017/database_name"
# https://www.mongodb.com/docs/manual/reference/connection-string/
# mongodb+srv://myDatabaseUser:D1fficultP%40ssw0rd@mongodb0.example.com/?authSource=admin
#mongodb://myDatabaseUser:D1fficultP%40ssw0rd@mongodb0.example.com:27017,mongodb1.example.com:27017,mongodb2.example.com:27017/?authSource=admin&replicaSet=myRepl
# mongodb://myDatabaseUser:D1fficultP%40ssw0rd@mongodb0.example.com:27017/?authSource=admin

client = motor.motor_asyncio.AsyncIOMotorClient(
    db_connection
)
db = client[db_name]


async def get_next_id(name: str)->int:
    counter = await db.counter.find_one_and_update(
        {"type": name},
        {"$inc": {"seq": 1}},
        return_document=True,
        upsert=True,
    )
    return counter["seq"]
