# Import necessary libraries
from web3 import Web3, HTTPProvider
from hexbytes import HexBytes
import secrets
from eth_account.messages import encode_defunct
import logging
logging.basicConfig(level=logging.INFO)
# Set up web3 connection
from eth_keys import keys

w3 = Web3(Web3.HTTPProvider(""))

# Define function to verify signature
def verify_signature(address, message, signature):
    try:
        mesage = encode_defunct(text=message)
        recovered_address = w3.eth.account.recover_message(mesage, signature=HexBytes(
            signature))
        if address.lower() == recovered_address.lower():
            return True
        else:
            return False
    except Exception as e:
        return False

def get_eth_address():
    # 生成一个新的私钥
    private_key = keys.PrivateKey(secrets.token_bytes(32))

    # 从私钥派生出公钥
    public_key = private_key.public_key

    # 从公钥派生出以太坊地址
    eth_address = public_key.to_checksum_address()
    return (private_key,public_key,eth_address)

