import logging
import os
import shutil
import time
import uuid
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from agent.models.base import GenericResponseModel
from ulid import ULID
from fastapi.encoders import jsonable_encoder

from agent.models.op_log import OpLog
from pydantic import BaseModel, Field
from beanie import Document
import random
import string
import secrets
from typing import TypeVar, List
from fastapi import Request
import hashlib


from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives import hashes

T = TypeVar('T')


max_size = 100 * 1024 * 1024  # 100MB
backup_count = 5  # 保留5个备份文件

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 创建RotatingFileHandler对象
log_file = 'log_file.log'

# 创建屏幕处理器
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)

# 创建文件处理器
file_handler = logging.FileHandler('log_file.log')
file_handler.setLevel(logging.INFO)
# 创建格式化器
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
# 将格式化器添加到文件处理器
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# 将文件处理器添加到logger对象
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

# 检查日志文件大小并进行轮转
if os.path.getsize(log_file) > max_size:
    # 关闭当前的文件处理器
    file_handler.close()

    # 重命名当前的日志文件
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    backup_file = f'{log_file}.{timestamp}'
    shutil.move(log_file, backup_file)

    # 创建新的文件处理器
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)





def generate_random_string(length):
    letters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(letters) for _ in range(length))


def error_return(code, message, data:T=None):
    return GenericResponseModel(code=code, message= message,result=data)


def success_return(data: T=None):
    return GenericResponseModel(result=data)


def succ(data) -> T:
    data = {"code": 0, "message": "success", "result": data}
    return T(**data)


def get_unique_id():
    return str(ULID())
def get_session_id():
    random_uuid = uuid.uuid4()
    return calculate_sha256(str(random_uuid))


def calculate_md5(data):
    md5_hash = hashlib.md5()
    md5_hash.update(data.encode('utf-8'))
    return md5_hash.hexdigest()
def calculate_sha256(data):
    sha256_hash = hashlib.sha256()
    sha256_hash.update(data.encode('utf-8'))
    return sha256_hash.hexdigest()

def get_mtime():
    return int(round(time.time() * 1000))


def encode_input(data) -> dict:
    data = jsonable_encoder(data)
    data = {k: v for k, v in data.items() if v is not None and v != "" and v != []}
    return data

def get_decimal(value, precis="0.00000001"):
    precision = Decimal(precis)
    result = Decimal(value).quantize(precision, rounding=ROUND_HALF_UP)
    return result
async def op_log(msg, uid: str(""), extra={}):
    logging.info(msg)
    await OpLog.record(msg, uid, extra)


from email_validate import validate, validate_or_fail


def is_email_validate(email):
    return validate(
        email_address=email,
        check_format=True,
        check_blacklist=False,
        check_dns=False,
        dns_timeout=10,
        check_smtp=False,
        smtp_debug=False)


def fill_model_from_obejct(base_info: BaseModel, doc: Document):
    for field in base_info.model_fields:
        if hasattr(doc, field):
            setattr(base_info, field, getattr(doc, field))
    return base_info


def get_host(request: Request):
    client_host = request.headers.get("X-Forwarded-For")
    if client_host:
        return client_host
    else:
        return request.client.host
        # user_ip = request.headers.get('CF-Connecting-IP')
        # city = request.headers.get('CF-IPCity')
        # country = request.headers.get('CF-IPCountry')
        # return request.headers.get("host")


def filter_empty_value(form:BaseModel):
    filter_items = {k: v for k, v in form.model_dump().items() if
                    (v is not None and v != "" and v != [] and v != {}) and v != 0}
    return filter_items


def aes_256_encrypt(key, plaintext):
    # 生成一个随机的初始化向量
    iv = b'0123456789abcdef'

    # 使用PKCS7填充方式进行填充
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(plaintext) + padder.finalize()

    # 创建AES-256加密器
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    # 加密数据
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()

    return ciphertext


def aes_256_decrypt(key, ciphertext):
    # 生成一个随机的初始化向量
    iv = b'0123456789abcdef'

    # 创建AES-256解密器
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()

    # 解密数据
    decrypted_data = decryptor.update(ciphertext) + decryptor.finalize()

    # 使用PKCS7填充方式进行去填充
    unpadder = padding.PKCS7(128).unpadder()
    plaintext = unpadder.update(decrypted_data) + unpadder.finalize()

    return plaintext

def rsa_decode(encrypted_data,private_key):
    # 解密数据
    decrypted_data = private_key.decrypt(
        encrypted_data,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return decrypted_data.decode()


def gen_rsa_pair():# 生成一对RSA公私钥
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    # 提取私钥
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    # 提取公钥
    public_key = private_key.public_key()
    public_key_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    # 存储私钥和公钥
    with open('private_key.pem', 'wb') as f:
        f.write(private_key_pem)

    with open('public_key.pem', 'wb') as f:
        f.write(public_key_pem)


def get_current_time():
    return int(time.time() * 1000) + datetime.now().microsecond // 1000
