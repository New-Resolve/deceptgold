from cyclopts import App

from deceptgold.commands.user import users_app

app = App()

app.command(users_app)


if __name__ == "__main__":
    app()
