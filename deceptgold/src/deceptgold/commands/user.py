from cyclopts import App, Parameter, Group
from typing import Annotated

users_app = App(name="user", help="User management")

hidden_group = Group(name="Comandos Ocultos", show=False)

@users_app.command(name="--secret", group=hidden_group)
def secret_command():
    """
    Comando secreto que não aparece na ajuda padrão.
    """
    print(f"Este é um comando secreto da aplicacao! ")


@users_app.command(name="--register", help="Create registration of the user.")
def register(apikey: Annotated[str, Parameter(help="Chave de API necessária para autenticação.")]):
    print(f"Registrate of: {apikey}")

