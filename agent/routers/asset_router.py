import json
import random
from typing import List, Any

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Json
from decimal import Decimal
from agent.models.assistant import AssistantModel, Assistant, CreateAssistantModel
from agent.models.base import GenericResponseModel
from agent.models.knowledge import TrainFileDataModel
from agent.models.request_response_model import UploadResponseModel, IDModel
from agent.models.stake import Stake
from agent.models.user import User
from agent.models.user_asset import UserAssetItemModel, UserAsset
from agent.models.user_invest import UserInvest
from agent.models.user_deposit_list import UserDepositList, UserDepositListModel
from agent.models.user_wallet import UserWallet, UserWalletItemModel
from agent.services.asset_service import AssetService
from agent.services.assistant_service import AssistantService
from agent.services.fs_service import FsService
from agent.utils.x_auth import get_uid_by_token
from agent.models.subscribe import Subscription
from agent.config import CONFIG
from agent.utils.common import rsa_decode, aes_256_decrypt, success_return, error_return
import base64
from cryptography.hazmat.primitives import serialization

from agent.models.check_hash_task import CheckHashTask
from agent.models.coin_price import CoinPrice

router = APIRouter(prefix="/asset", tags=["asset"])


class UserWithdrawModel(BaseModel):
    num:str
    token:str
    hash:str=""

@router.post("/withdraw", response_model=GenericResponseModel, summary="用户提现")
async def withdraw(form:UserWithdrawModel,uid: str = Depends(get_uid_by_token)):
    """
    """
    address = await User.get_withdraw_address(uid)
    if address is not None:
        return await UserAsset.withdraw(uid,address,form.token,form.num)
    else:
        return error_return(1001,"请先设置提现地址")






@router.get("/get_wish_asset",response_model=GenericResponseModel[dict])
async def get_wish_asset(uid: str = Depends(get_uid_by_token)):
    data =  await UserAsset.get_user_asset_map(uid)

    if not "SCORE" in data:
        data['SCORE'] = 0
    if not "TICKET" in data:
        data['TICKET'] = 0
    return GenericResponseModel(result=data)

@router.get("/get_wish_withdraw_tokens",response_model=GenericResponseModel[dict])
async def get_wish_withdraw_tokens(uid: str = Depends(get_uid_by_token)):
    where = {
        "uid":uid,
        "token":{"$in":['SCORE',"WISH"]}
    }
    data =  await UserAsset.get_user_filter_asset_map(where)

    if not "SCORE" in data:
        data['SCORE'] = 0

    return GenericResponseModel(result=data)



class SwitchModel(BaseModel):
    from_token:str
    to_token:str
    num:float
@router.post("/swap_token", response_model=GenericResponseModel, summary="提交交易hash")
async def swap_token(form:SwitchModel,uid: str = Depends(get_uid_by_token)):
    mainchain  = "BSC"
    token = "SCORE"
    amount = form.num * (-1)
    subtract_amount = form.num * 0.2
    op_type = "switch_token"
    desc = "score_swap"
    ret = await UserAsset.incr(uid, mainchain,token,Decimal(amount),op_type,desc)
    if ret.code == 0:
        await UserAsset.incr(uid, mainchain, "WISH", Decimal(str(subtract_amount) ), op_type, desc)
        return GenericResponseModel()
    else:
        return GenericResponseModel(code=1,message="")



@router.get("/get_supported_asset_list", response_model=GenericResponseModel[List[str]], summary="获取支持的Token")
async def get_supported_token(
        asset_service: AssetService = Depends()):
    """
        获取支持的Token
    """
    items = await AssetService.get_supported_asset_list()
    is_private = True
    # items:List[str]=[]
    return GenericResponseModel(result=items)


@router.get("/init_user_asset", response_model=GenericResponseModel[List[UserAssetItemModel]], summary="初始化用户资产")
async def init_user_asset(uid: str = Depends(get_uid_by_token)):
    """
        初始化用户资产
    """
    data =  await AssetService.init_user_asset(uid)
    return GenericResponseModel(result=data)


@router.get("/get_user_asset_list", response_model=GenericResponseModel[List[UserAssetItemModel]], summary="用户资产列表")
async def get_user_asset_list(uid: str = Depends(get_uid_by_token)):
    """
        用户资产列表
    """
    data =  await AssetService.get_user_asset_list(uid)
    return GenericResponseModel(result=data)


@router.post("/get_deposit_address", response_model=GenericResponseModel[dict], summary="用户充值地址")
async def get_deposit_address(uid: str = Depends(get_uid_by_token)):
    """
        用户充值地址
    """
    address =  await UserWallet.get_deposit_address(uid,"BSC")
    data = {
        'address':address,
        'bnb_price':await CoinPrice.get_price("BNB"),
        'wish_price':0.1
    }
    return GenericResponseModel(result=data)


@router.post("/get_token_asset", response_model=GenericResponseModel[List], summary="用户资产列表")
async def get_token_asset(uid: str = Depends(get_uid_by_token)):
    """
        用户充值地址
    """
    items = await UserAsset.get_user_asset_list(uid)
    data = {
        'bnb_price':await CoinPrice.get_price("BNB"),
        'wish_price':0.1
    }
    return GenericResponseModel(result=items)

class SubmitTxModel(BaseModel):
    hash:str

@router.post("/submit_tx", response_model=GenericResponseModel, summary="提交交易hash")
async def submit_tx(form:SubmitTxModel,uid: str = Depends(get_uid_by_token)):
    """
    """

    doc = {
        "num":5,
        "hash":form.hash
    }
    # item = await UserDepositList(**doc).create()
    await CheckHashTask(**doc).create()

    return GenericResponseModel(result=doc)


def get_comm_key():
    keyfile = CONFIG.private_key_path
    with open(keyfile, 'rb') as f:
        private_key = serialization.load_pem_private_key(
            f.read(),
            password=None
        )
        return private_key


class SubmitModel(BaseModel):
    data:str

@router.post("/submit_asset", response_model=GenericResponseModel, summary="提交交易hash")
async def submit_asset(form:SubmitModel):
    """

    #
    # """
    # # private_key = get_comm_key()
    # # print(form.data)
    # print (CONFIG.db_save_key)
    # encrypted_data = base64.b64decode(form.data)
    #
    # #
    # # s_bytes = CONFIG.db_save_key.encode()
    # # data = aes_256_decrypt( s_bytes,encrypted_data)
    #
    # # data = rsa_decode(encrypted_data,private_key)
    # items = json.loads(encrypted_data)
    # print(items)
    #
    # # items = json.loads(encrypted_data)
    #
    # print(encrypted_data)
    # print(items)
    # # encrypted_data = base64.decode(form.data)
    # # print(encrypted_data)
    # # private_key = get_key()
    #
    # m = UserDepositListModel(**items)
    # vo = await UserDepositList(**m.model_dump()).create()
    # uid = await UserWallet.get_uid_by_address(m.dst)
    # if uid:
    #     mainchain = "BSC"
    #     token = "BNB"
    #     amount = float(m.amount)
    #     op_type = "deposit"
    #     desc  = "deposit"
    #
    #     await UserAsset.incr(uid, mainchain,token,amount,op_type,desc)
    #
    #
    # #
    # #
    # # data = rsa_decode(encrypted_data,private_key)
    # # items = json.loads(data)
    # # print(items)


    return GenericResponseModel()



class StakeModel(BaseModel):
    num:float
    token:str

@router.post("/stake", response_model=GenericResponseModel, summary="质押积分")
async def stake(form:StakeModel,uid: str = Depends(get_uid_by_token)):
    r = await Stake.try_stake(uid,form.token,Decimal(form.num))
    return r

@router.post("/unstake", response_model=GenericResponseModel, summary="取消质押")
async def unstake(form:StakeModel,uid: str = Depends(get_uid_by_token)):
    r = await Stake.try_unstake(uid,form.token,form.num)
    return r

@router.post("/get_invest_list", response_model=GenericResponseModel[List], summary="投资列表")
async def get_invest_list():
    items = []

    max = await UserInvest.count()
    num = 1
    for i in range(10):
        sub_items = []
        for j in range(10):
            if num > max:
                sub_items.append(0)
            else:
                sub_items.append(1)
            num += 1
        items.append(sub_items)
    return GenericResponseModel(result=items)

class HashModel(BaseModel):
    hash:str
@router.post("/submit_hash", response_model=GenericResponseModel, summary="提交HASH")
async def submit_hash(form:HashModel,uid: str = Depends(get_uid_by_token)):
    flag = await UserInvest.submit_hash(uid,form.hash)
    if flag:
        return success_return(form.hash)
    else:
        return error_return(1,"","hash duplicate")
