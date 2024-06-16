from dotenv import load_dotenv
import os

def get_redis_config():
    load_dotenv()
    return os.getenv("REDIS_HOST"), os.getenv("REDIS_PORT"), os.getenv("REDIS_PASSWORD")

def get_db_config():
    load_dotenv()
    return os.getenv("DB_HOST"), os.getenv("DB_PORT"), os.getenv("DB_USER"), os.getenv("DB_PASSWORD"), os.getenv("DB_NAME")

def get_db_connection():
    load_dotenv()
    return os.getenv("DB_CONNECTION")