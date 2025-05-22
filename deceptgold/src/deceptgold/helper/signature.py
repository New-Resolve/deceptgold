import json
from eth_utils import keccak
from eth_account import Account
from eth_account.messages import encode_defunct

def generate_new_keys():
    account = Account.create()
    private_key = account.key.hex()
    public_address = account.address
    print("New Private Key:", private_key)
    print("New Public Key:", public_address)

"""
WARNING: INTENTIONAL USE OF HARDCODED PRIVATE KEY
This private key is purposefully embedded to ensure that
the honeypot generates consistent and verifiable signatures by a smart contract.
The security of the key is guaranteed by other means such as via pyarmor
ATTENTION: Change private key when repository goes to new private version control.
"""
PRIVATE_KEY = "519216cdca0785ea8f01906bb177a987ad8b0181c7dec347f5c0663e8170fb43" # nose: B105 - Intentional use of hardcoded key for cryptographic signature

"""
This is the value that will exist within the smart contract to prove the off-chain signature of the value 
sent by the user. It is through the asymmetric key that the system guarantees the legitimacy of the reward.
"""
EXPECTED_ADDRESS = "0xfA6a145a7e1eF7367888A39CBf68269625C489D2"

def generate_signature_and_hash(json_data):
    json_string = json.dumps(json_data, separators=(',', ':'), sort_keys=True)
    message_hash = keccak(text=json_string)
    signed_message = Account.sign_message(encode_defunct(hexstr=message_hash.hex()), private_key=PRIVATE_KEY)
    return signed_message.signature, message_hash, json_string

def verify_signature(signature, message_hash, expected_address=EXPECTED_ADDRESS):
    message = encode_defunct(hexstr=message_hash.hex())
    recovered_address = Account.recover_message(message, signature=signature)
    return recovered_address == expected_address