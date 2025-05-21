import logging
import os
import json

from cyclopts import App, Parameter, Group
from typing import Annotated
from web3 import Web3

from deceptgold.configuration.config_manager import update_config, get_config
logger = logging.getLogger(__name__)

users_app = App(name="user", help="User management")

hidden_group = Group(name="Comandos Ocultos", show=False)

@users_app.command(name="--secret", group=hidden_group)
def secret_command():
    """
    Secret command that does not appear in standard help.
    """
    logger.info(f"The secret function of the application was performed in the users module!")
    print(f"The secret function of the application was performed in the users module!")


@users_app.command(name="--my-address", help="Create registration of the user. Insert to address wallet.")
def register(my_address: Annotated[str, Parameter(help="User's wallet address. User's public address.")]):
    """
    Mandatory command to collect your rewards
    :param my_address: your address wallet pattern ERC20 example: 0x0105d8Ceab792bfece1b2994B71992Af56930081
    """
    update_config("address", my_address)

    update_config('net_rpc', 'https://data-seed-prebsc-1-s1.binance.org:8545/', 'blockchain')
    update_config('key_public_expected_signer', '0xfA6a145a7e1eF7367888A39CBf68269625C489D2', 'blockchain')
    update_config('contract_token_address', '0x606c0fE69D437F42BfC11D3eec82F596cC02C02a', 'blockchain')
    update_config('contract_validator_address', '0x12485DAE42bFc5bF625f4Da5738847e79CFe2cAD', 'blockchain')

@users_app.command(name="--show-balance", help="Show deceptgold wallet value balance.")
def show_balance():
    """
    Return the value of the accumulation of deceptgold tokens that the user has in his wallet
    """
    w3 = Web3(Web3.HTTPProvider(get_config('blockchain', 'net_rpc')))
    try:
        root_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "resources"))
        with open(os.path.join(root_dir, "TokenContract.abi.json")) as f:
            abi_token = json.load(f)

        contract_address = Web3.to_checksum_address(get_config('blockchain', 'contract_token_address'))
        user_address = Web3.to_checksum_address(get_config('user', 'address'))

        contract_token = w3.eth.contract(address=contract_address, abi=abi_token)
        balance = contract_token.functions.balanceOf(user_address).call()
        decimals = contract_token.functions.decimals().call()
        balance_formatted = balance / (10 ** decimals)

        print(f"Balance: {balance_formatted} DGLD")
        print(f"Balance (base units): {balance}")
        print(f"Explorer: https://testnet.bscscan.com/address/{user_address}")
    finally:
        del w3