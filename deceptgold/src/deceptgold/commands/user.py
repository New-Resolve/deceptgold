import logging

from cyclopts import App, Parameter, Group
from typing import Annotated

from deceptgold.configuration.config_manager import update_config

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
    :param my_address: your address wallet pattern ERC20
    """
    update_config("address", my_address)
