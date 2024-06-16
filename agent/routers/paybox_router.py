from fastapi import APIRouter, Depends, Response

from agent.models.base import GenericResponseModel
from agent.models.paybox import CreatePayOrder, PayOrder, PayboxOrderModel
from agent.models.subscribe import Subscription
from agent.models.user import User
from agent.utils.common import success_return
from agent.utils.x_auth import get_uid_by_token

router = APIRouter(prefix="/paybox", tags=["paybox"])

import logging
import json
import time
import hashlib
import binascii
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from cryptography.hazmat.backends import default_backend

def verify(message, signature, public_key):
    try:
        public_key.verify(signature, message, ec.ECDSA(hashes.SHA256()))
        return True
    except Exception:
        return False

@router.post("/nabox_pay_confirm",response_model=GenericResponseModel,summary="交易到账通知")
async def nabox_pay_confirm(form:PayboxOrderModel ):
    current_time = int(time.time())
    if abs(current_time - form.send)> 10:
        logging.error("请求时间偏差")
        return GenericResponseModel(code=1,message="time error")
    pub_key = binascii.unhexlify("xxx")
    key = form.outerOrderNo+ str(form.sendTime)
    key_byte = key.encode('utf-8')
    sign = binascii.unhexlify(form.sign)
    try:
        # 使用 ECDSA 算法对签名进行验证。
        is_valid = verify(key_byte, sign, pub_key)

        logging.info("sign verify: %s", verify)
        if is_valid:
            logging.info("订单已完成")
            # 获取订单对象进行业务处理
        return "SUCCESS" if verify else "FAIL"
    except Exception as e:
        logging.error(str(e))
        return "FAIL"


#
@router.post("/create_pay_order",response_model=GenericResponseModel[str])
async def create_pay_order(form:CreatePayOrder,uid: str = Depends(get_uid_by_token)):
    """Get current user"""
    order_id = await PayOrder.create_order(uid,form)
    return GenericResponseModel(result=order_id)
