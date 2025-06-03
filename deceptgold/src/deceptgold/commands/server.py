import logging

from cyclopts import App, Parameter
from typing import Annotated

from deceptgold.configuration.opecanary import toggle_config

logger = logging.getLogger(__name__)

server_app = App(name="server", help="Module with options coming from the local server, machine or operating system.")


@server_app.command(name="--node_id", help="Provide the desired name for recognition of this machine for the entire deceptgold system.")
def register(node_id: Annotated[str, Parameter(help="The default recognized name is the hostname configured in your system's environment variables.")]):
    # Reuse of the configuration function. It is due to the reuse of code that the service name is device.
    toggle_config('device', 'node_id', node_id)
