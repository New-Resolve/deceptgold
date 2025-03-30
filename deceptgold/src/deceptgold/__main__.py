from cyclopts import App

from deceptgold.comandos.user import users_app

app = App()

app.command(users_app)


if __name__ == "__main__":
    app()
