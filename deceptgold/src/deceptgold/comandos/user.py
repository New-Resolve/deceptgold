from cyclopts import App, Parameter, Group
from typing import Annotated

users_app = App(name="user", help="User manager")

hidden_group = Group(name="Comandos Ocultos", show=False)

@users_app.command(name="--secret", group=hidden_group)
def secret_command():
    """
    Comando secreto que não aparece na ajuda padrão.
    """
    print(f"Este comando secreto da aplicacao")


@users_app.command(name="--register", help="Registra o usuário no sistema.")
def register(apikey: Annotated[str, Parameter(help="Chave de API necessária para autenticação.")]):
    print(f"Registrado para: {apikey}")

