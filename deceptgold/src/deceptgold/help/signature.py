import json
from eth_utils import keccak
from eth_account.messages import encode_defunct
from eth_account import Account

def generate_new_keys():
    account = Account.create()
    private_key = account.key.hex()
    public_address = account.address
    print("New Private Key:", private_key)
    print("New Public Key:", public_address)


PRIVATE_KEY = "519216cdca0785ea8f01906bb177a987ad8b0181c7dec347f5c0663e8170fb43"
EXPECTED_ADDRESS = "0xfA6a145a7e1eF7367888A39CBf68269625C489D2"

def generate_signature_and_hash(json_data):
    json_string = json.dumps(json_data, separators=(',', ':'), sort_keys=True)
    message_hash = keccak(text=json_string)
    message = encode_defunct(message_hash)
    signed_message = Account.sign_message(message, private_key=PRIVATE_KEY)
    return signed_message.signature, message_hash, json_string

def verify_signature(signature, message_hash, expected_address=EXPECTED_ADDRESS):
    message = encode_defunct(message_hash)
    recovered_address = Account.recover_message(message, signature=signature)
    return recovered_address == expected_address
