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
    Comando secreto que não aparece na ajuda padrão.
    """
    logger.info(f"Foi executado a função secreta da aplicação no módulo de usuarios!")
    print(f"Este é um comando secreto da aplicacao! ")


@users_app.command(name="--my-address", help="Create registration of the user. Insert to address wallet.")
def register(my_address: Annotated[str, Parameter(help="User's wallet address. User's public address.")]):
    update_config("address", my_address)
