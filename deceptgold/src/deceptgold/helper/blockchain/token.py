import os
import json
import logging
import warnings
import threading
import ast
import random
import glob
import tempfile

from web3 import Web3
from eth_account.messages import encode_defunct
from opencanary.logger import getLogger

from deceptgold.helper.helper import get_temp_log_path
from deceptgold.helper.signature import generate_signature_and_hash, verify_signature
from deceptgold.helper.blockchain.sender import Sender
from deceptgold.configuration.config_manager import update_config, get_config
from deceptgold.helper.fingerprint import get_machine_fingerprint

warnings.filterwarnings("ignore", category=UserWarning, module="eth_utils.functional")

"""
Example configuration:
{
    "user": {
        "address": "0x0105d8Ceab792bfece1b2994B71992Af56930081"
    },
    "blockchain": {
        "net_rpc": "https://data-seed-prebsc-1-s1.binance.org:8545/",
        "key_public_expected_signer": "0xfA6a145a7e1eF7367888A39CBf68269625C489D2",
        "contract_token_address": "0x606c0fE69D437F42BfC11D3eec82F596cC02C02a",
        "contract_validator_address": "0x12485DAE42bFc5bF625f4Da5738847e79CFe2cAD"
    }
}    
"""
try:
    BSC_TESTNET_RPC = get_config('blockchain', 'net_rpc')
    w3 = Web3(Web3.HTTPProvider(BSC_TESTNET_RPC))

    PRIVATE_KEY, SENDER = Sender(w3).get_safe_key_sender()

    pending_nonce = w3.eth.get_transaction_count(SENDER, 'pending')
    latest_nonce = w3.eth.get_transaction_count(SENDER, 'latest')

    if not w3.is_connected():
        raise Exception('Not connected network rpc.')

    KEY_PUBLIC_EXPECTED_SIGNER = get_config('blockchain', 'key_public_expected_signer')
    CONTRACT_TOKEN_ADDRESS = Web3.to_checksum_address(get_config('blockchain', 'contract_token_address'))
    CONTRACT_VALIDATOR_ADDRESS = Web3.to_checksum_address(get_config('blockchain', 'contract_validator_address'))

    if w3.eth.get_code(Web3.to_checksum_address(CONTRACT_TOKEN_ADDRESS)) == b'':
        raise Exception('Invalid contract token address.')

    if w3.eth.get_code(Web3.to_checksum_address(CONTRACT_VALIDATOR_ADDRESS)) == b'':
        raise Exception('Invalid contract validator address.')

except Exception as e:
    pass


def call_first_upload_contract():
    """
    Attention: every time you update a system contract or create a new one, this function needs to be called.
    """
    root_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "resources"))
    with open(os.path.join(root_dir, "TokenContract.abi.json")) as f:
        abi_token = json.load(f)

    contract_token = w3.eth.contract(address=CONTRACT_TOKEN_ADDRESS, abi=abi_token)

    current_validator = contract_token.functions.validatorContract().call()
    if current_validator.lower() != CONTRACT_VALIDATOR_ADDRESS.lower():
        print("Updating validatorContract token...")
        tx_set = contract_token.functions.setValidatorContract(CONTRACT_VALIDATOR_ADDRESS).build_transaction({
            'from': SENDER,
            'nonce': w3.eth.get_transaction_count(SENDER, 'pending'),
            'gas': 100000,
            'gasPrice': w3.to_wei('10', 'gwei')
        })

        signed_tx_set = w3.eth.account.sign_transaction(tx_set, private_key=PRIVATE_KEY)
        tx_hash_set = w3.eth.send_raw_transaction(signed_tx_set.raw_transaction)
        receipt_set = w3.eth.wait_for_transaction_receipt(tx_hash_set)
        print(f"ValidatorContract definido no token! {receipt_set}")
        print(f"Explorer: https://testnet.bscscan.com/tx/{tx_hash_set.hex()}")
    else:
        print("ValidatorContract configuration exists")


def farm_deceptgold(wallet_address_target, request_honeypot):
    module_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "resources"))
    abi_path = os.path.join(module_dir, "ValidatorContract.abi.json")
    with open(abi_path) as f:
        abi_validator = json.load(f)

    contract_validator = w3.eth.contract(address=CONTRACT_VALIDATOR_ADDRESS, abi=abi_validator)

    signature, json_hash, _ = generate_signature_and_hash(request_honeypot)

    if not verify_signature(signature=signature, message_hash=json_hash):
        raise Exception("Signature verification failed!")

    message_hash = json_hash
    signature_bytes = signature
    message = encode_defunct(hexstr=message_hash.hex())
    signer_address = w3.eth.account.recover_message(message, signature=signature_bytes)

    if KEY_PUBLIC_EXPECTED_SIGNER != signer_address:
        raise Exception(f'Validation spoke in the comparison of expectations: {signer_address} != {KEY_PUBLIC_EXPECTED_SIGNER}')

    tx = contract_validator.functions.claimToken(json_hash, signature, wallet_address_target).build_transaction({
        'from': SENDER,
        'nonce': w3.eth.get_transaction_count(SENDER, 'pending'),
        'gas': 100000,
        'gasPrice': w3.to_wei('5', 'gwei')
    })

    try:
        # Import is necessary because the print function needs to be loaded before calling the function that collects the config. If the import is loaded when starting the module, some opencanary prints are invoked. By importing in this location, the native print function is overwritten before this loading.
        # noqa: E402
        # pylint: disable=import-outside-toplevel
        from opencanary.config import config
        logger = getLogger(config)

        try:
            signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_hash_0x = f'0x{tx_hash.hex()}'

            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

            logging.info("Waiting for transaction confirmation...")
            logs = contract_validator.events.SignerRecovered().process_receipt(receipt)
            for log in logs:
                logging.info("Signature recovered on the contract: " + log['args']['signer'])

            logger.log({"reward": f"Transaction confirmed in the block: " + str(receipt.blockNumber), "token": "deceptgold"}, retry=False)
            logger.log({"reward": f"Transaction: {tx_hash_0x}", "token": "deceptgold"}, retry=False)
            logger.log({"reward": f"Used gas: " + str(receipt.gasUsed), "token": "deceptgold"}, retry=False)
            logger.log({"reward": f"Status: {'Success' if receipt.status == 1 else 'Failure'}", "token": "deceptgold"}, retry=False)
            logger.log({"reward": f"Explorer: https://testnet.bscscan.com/tx/{tx_hash_0x}", "token": "deceptgold"}, retry=False)
        except Exception as error:
            msg_error = {"reward_error": f"{error}", "token": "deceptgold"}
            logger.log(msg_error, retry=False)

    except Exception as g_error:
        print(g_error)

def get_mod():
    return 10

def get_count_reward_first():
    return 1_000

def get_count_reward_second():
    return 10

def get_count_reward_final():
    return get_count_reward_first() * get_count_reward_second()


def search_stack_file():
    all_files = glob.glob(os.path.join(tempfile.gettempdir(), "*.stack"))
    return all_files[0] if all_files else None

CONFIG_FILE = get_temp_log_path(''.join(random.choices('abcdef0123456789', k=7)) + '.stack')
pre_file_stack = search_stack_file()
if pre_file_stack:
    CONFIG_FILE = pre_file_stack


pass_fingerprint = get_machine_fingerprint()
list_logs = eval(get_config(key='hash', module_name_honeypot='cache', passwd=pass_fingerprint, default='set()', file_config=CONFIG_FILE))
list_count = 0
list_logs_lock = threading.Lock()
reward_triggered = False

def get_reward(log_honeypot):
    global reward_triggered
    global list_count

    user_wallet = get_config("user", "address", None)
    if not user_wallet:
        return None

    try:
        # Ignore system boot logs as they are not real attacks.
        log_json = json.loads(log_honeypot)
        if 'msg' in log_json['logdata'].keys():
            msg = ast.literal_eval(log_json['logdata']['msg'])
            if 'added service from class' in msg['logdata']:
                return None
        log_hash = hash(json.dumps(log_json, sort_keys=True))
        with list_logs_lock:
            if reward_triggered:
                return None

            if log_hash not in list_logs:
                list_logs.add(log_hash)
                list_count = len(list_logs)

            if list_count % get_mod() == 0:
                update_config(key='hash', value=str(list_logs), module_name='cache', passwd=pass_fingerprint, config_file=CONFIG_FILE)

            if list_count >= get_count_reward_final():
                reward_triggered = True
                update_config(key='hash', value=str(set()), module_name='cache', passwd=pass_fingerprint, config_file=CONFIG_FILE)
                threading.Thread(target=handle_reward_async, args=(log_honeypot,), daemon=True).start()
                list_logs.clear()
    except Exception as e:
        logging.error(f"[get_reward] Erro: {e}")

def handle_reward_async(log_honeypot):
    global reward_triggered
    try:
        address_wallet_user = get_config('user', 'address')
        farm_deceptgold(address_wallet_user, log_honeypot)
        with list_logs_lock:
            list_logs.clear()
            reward_triggered = False
    except Exception as e:
        logging.error(f"[handle_reward_async] Erro: {e}")
