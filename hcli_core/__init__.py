import os
import inspect
import base64

from hcli_core import logger
from hcli_core.auth.cli import credential
from hcli_core import hcliserver
from hcli_core import config

log = logger.Logger("hcli_core")
log.setLevel(logger.INFO)


def connector(plugin_path=None, config_path=None):

    cm = credential.CredentialManager(config_path)
    server_manager = hcliserver.LazyServerManager(plugin_path, config_path)

    # We select a response server based on port
    def port_router(environ, start_response):
        server_port = int(environ.get('SERVER_PORT', 0))
        path = environ.get('PATH_INFO', '/')

        server_info = server_manager.get_server_for_request(server_port, path)

        # Get or initialize the appropriate server
        if not server_info:
            log.warning(f"Request received on unconfigured port: {server_port}")
            start_response('404 Not Found', [('Content-Type', 'text/plain')])
            return [b'No server configured for this port']

        server_type, server = server_info

        # Debug logging
        log.debug(f"{environ}")

        # Set server context and route request
        config.ServerContext.set_current_server(server_type)
        return server(environ, start_response)

    return port_router
