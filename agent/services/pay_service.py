import requests

from agent.config import CONFIG
from agent.models.apple_order import AppleOrder
from agent.models.base import GenericResponseModel
from agent.models.user import User


class PayService:
    llm: None


    @classmethod
    async def verify_ios_pay(self,uid,order_id,ticket):
        # 生成订单请求
        request = {
            'receipt-data': ticket,
            'password': 'F532b506a9024a35bc5afa7496296dee'  # 共享密钥
        }
        order = {'sandbox': True}

        # 发送请求到苹果服务器
        url = 'https://sandbox.itunes.apple.com/verifyReceipt' if order[
            'sandbox'] else 'https://buy.itunes.apple.com/verifyReceipt'
        response = requests.post(url, json=request)



        doc = {
            "uid":uid,
            "order_id": order_id,
            "ticket": ticket,
            "info": response.content
        }
        response = response.json()

        await AppleOrder(**doc).create()
        print(response)
        if response['status'] == 0:
            # 订单验证成功，处理购买信息
            purchase_info = response['receipt']['in_app'][0]
            transaction_id = purchase_info['transaction_id']
            product_id = purchase_info['product_id'].lower()
            purchase_date = purchase_info['purchase_date']
            if product_id == "aibuddhayearly1":
                pass
                # UserModel.getInstance().tbl(app).updateOne({'uid': uid},
                #                                            {'$set': {'paid_type': 'forever', 'days_left': 100000}})
                # paid_type = "forever"
                # days_left = 100000
                # msg = "购买永久套餐"
                # OpLogModel.getInstance().record(app, uid, msg)
            elif product_id == "aibuddha1":
                pass
                # paid_type = "week"
                # days_left = 7
                # UserModel.getInstance().tbl(app).findOneAndUpdate({'uid': uid}, {'$set': {'paid_type': 'week'},
                #                                                                  '$inc': {'days_left': 7}})
                # msg = "订阅周套餐"
                # OpLogModel.getInstance().record(app, uid, msg)
            else:
                paid_type = "product_id unknown"
                days_left = 0
            data = {

            }
            await User.set_vip_level(uid)
            # this.tbl(app).updateOne({'order_id': order_id}, {'$set': purchase_info})
            #
            # ret = RetUtil.succRet({'paid_type': paid_type, 'days_left': days_left})
            return   GenericResponseModel()

        else:
            # 订单验证失败，处理错误信息
            error_code = response['status']
            error_message = response['status_message']
            data = {

            }
            return   GenericResponseModel(code=error_code,message=error_message)




