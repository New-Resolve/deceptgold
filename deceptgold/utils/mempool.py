import time

from web3 import Web3

from deceptgold.configuration.config_manager import get_config
from deceptgold.help.blockchain.sender import Sender

def clean_mempool():
    BSC_TESTNET_RPC = get_config('blockchain', 'net_rpc')
    w3 = Web3(Web3.HTTPProvider(BSC_TESTNET_RPC))

    private_key, sender = Sender(w3).get_safe_key_sender()

    nonce_confirmed = w3.eth.get_transaction_count(sender, 'latest')
    nonce_pending = w3.eth.get_transaction_count(sender, 'pending')

    if nonce_pending == nonce_confirmed:
        return None

    for nonce in range(nonce_confirmed, nonce_pending):
        tx = {
            'nonce': nonce,
            'to': sender,
            'value': 0,
            'gas': 21000,
            'gasPrice': w3.to_wei('50', 'gwei'),  # greater than previous
        }

        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        try:
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            print(f"Replacing nonce {nonce} with tx: {tx_hash.hex()}")
            time.sleep(1)
        except Exception as e:
            print(f"Error replacing nonce {nonce}: {e}")


if __name__ == '__main__':
    clean_mempool()