import os
import inspect
import base64

from hcli_core import config
from hcli_core.auth.cli import credential
from hcli_core import server

log = logger.Logger("hcli_core")

def connector(plugin_path=None, config_path=None):

    absolute_plugin_path = None
    absolute_config_path = None
    absolute_credentials_path = None
    if(plugin_path is not None):
        absolute_plugin_path = os.path.abspath(plugin_path)
    if(config_path is not None):
        absolute_config_path = os.path.abspath(config_path)
        absolute_credentials_path = os.path.join(os.path.dirname(absolute_config_path), "credentials")
    cm = credential.CredentialManager(absolute_credentials_path)
    server_manager = server.LazyServerManager(absolute_plugin_path, absolute_config_path)

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
