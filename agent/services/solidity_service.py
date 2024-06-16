import json
import os

import solcx
import web3
from solcx.exceptions import SolcError
from web3.middleware import geth_poa_middleware

from agent.models.file_meta import FileMetadata, SoldityFileMeta
from agent.utils.common import error_return, success_return
from dotenv import load_dotenv
import os

# w3 = web3.Web3(web3.HTTPProvider("http://127.0.0.1:8545"))

class SolidtyService:
    def __int__(self):
        self.w3 =  web3.Web3(web3.HTTPProvider("http://127.0.0.1:8545"))
        # self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    def get_key(self,mainchain):
        load_dotenv()
        if mainchain  == "ETH":
            key = "BSC_KEY"
        elif mainchain == "BSC":
            key = "BSC_KEY"
        elif mainchain == "BSC_TEST":
            key = "BSC_TEST_KEY"
        elif mainchain == "GOERLI":
            key = "GOERLI_KEY"
        else:
            return None;

        # return os.getenv(key)
        return "41f3b94d63a5b74c69fcb27ad65a7a95cc3be246ec43326ade24d25457e23eac"

    def get_web3(self,mainchain):
        if mainchain == "ETH":
            key = "ETH"
        elif mainchain == "BSC":
            key = "BSC_RPC_URL"
        elif mainchain == "BSC_TEST":
            key = "BSC_TEST_RPC_URL"
        elif mainchain == "HECO":
            return  web3.Web3(web3.HTTPProvider("http://"))
        elif mainchain == "GOERLI":
            key = "GOERLI_RPC_URL"
        else:
            return None
        url = os.getenv(key)
        url  = "https://goerli.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161"
        print(key,url,"url")
        return web3.Web3(web3.HTTPProvider(url))

    def get_spec(self,file_id,source):
        spec = {
            "language": "Solidity",
            "sources": {
                file_id: {
                    "urls": [
                        source
                    ]
                }
            },
            "settings": {
                "optimizer": {
                    "enabled": True
                },
                "outputSelection": {
                    "*": {
                        "*": [
                            "metadata", "evm.bytecode", "abi"
                        ]
                    }
                }
            }
        };
        return spec

    async def compile(self,file_id,contract_name):
        file = await SoldityFileMeta.get(file_id)
        if file is None:
            return error_return(1,"File not found")
        else:
            if os.path.isfile(file.filepath):
                spec = self.get_spec(file_id,file.filepath)
                try:
                    out = solcx.compile_standard(spec, allow_paths=".");
                    # print(out)
                    abi = out['contracts'][file_id][contract_name]['abi']
                    bytecode = out['contracts'][file_id][contract_name]['evm']['bytecode']['object']

                    file.version = str(solcx.get_solc_version())
                    file.abi = json.dumps(abi)
                    file.spec = json.dumps(spec)
                    file.bytecode = bytecode
                    file.contract_name = contract_name
                    file.status=2
                    # print(type(solcx.get_solc_version()))
                    # print(file)
                    await file.save()

                    return success_return(out)
                except SolcError as e:
                    return error_return(2, e)


        return error_return(2, "Compiler error")

    async def deploy(self,file_id,mainchain):
        file = await SoldityFileMeta.get(file_id)
        if file is None:
            return error_return(1, "File not found")
        if file.status != 2:
            return error_return(1, "File not found")
        w3 = self.get_web3(mainchain)
        key = self.get_key(mainchain)
        print(w3)
        print(key)
        acct = w3.eth.account.from_key(key)
        abi = json.loads(file.abi)
        bytecode = file.bytecode
        print(abi)
        print(bytecode)
        # return success_return(abi)
        contract = w3.eth.contract(abi=abi, bytecode=bytecode)
        txn = contract.constructor().build_transaction(
            {"from": acct.address,
             'nonce': w3.eth.get_transaction_count(acct.address),
             'gas': 3000000,
             'gasPrice': w3.to_wei('21', 'gwei')
            }

        );
        signed = acct.signTransaction(txn) # 交易签名
        tx = w3.eth.send_raw_transaction(signed.rawTransaction) # 交易发送
        tx_hash = tx.hex()


        # tx_hash = contract.constructor().transact({'from': acct.address})
        print(tx_hash)

        return success_return(tx_hash)


