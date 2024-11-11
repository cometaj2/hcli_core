import os
import inspect

from hcli_core import logger
from hcli_core import hcliapp

log = logger.Logger("hcli_core")
log.setLevel(logger.INFO)


def connector(plugin_path=None, config_path=None):

    # Initialize core application
    log.info("================================================")
    log.info(f"Core HCLI application:")
    log.info(f"{plugin_path}")
    coreapp = hcliapp.HCLIApp("core", plugin_path, config_path)
    core_server = coreapp.server()

    # Initialize management application
    root = os.path.dirname(inspect.getfile(lambda: None))
    mgmt_plugin_path = os.path.join(root, 'auth', 'cli')
    log.info("================================================")
    log.info(f"Management HCLI application:")
    log.info(f"{mgmt_plugin_path}")
    mgmtapp = hcliapp.HCLIApp("management", mgmt_plugin_path, config_path)
    mgmt_server = mgmtapp.server()

    # We select a response server based on port
    def port_router(environ, start_response):
        server_port = environ.get('SERVER_PORT')

        # Get authentication info from WSGI environ
        auth_info = environ.get('HTTP_AUTHORIZATION', '')

        # If using Basic auth, it will be in format "Basic base64(username:password)"
        if auth_info.startswith('Basic '):
            import base64
            # Extract and decode the base64 credentials
            encoded_credentials = auth_info.split(' ')[1]
            decoded = base64.b64decode(encoded_credentials).decode('utf-8')
            username = decoded.split(':')[0]

            # Store username in environ for downstream handlers
            environ['REMOTE_USER'] = username
            config.ServerContext.set_current_user(username)

        # If using Bearer auth, it will be in format "Bearer hcoak_base64(random)"
        if auth_info.startswith('Bearer '):
            # Store username in environ for downstream handlers
            environ['REMOTE_USER'] = "api key bearer"
            config.ServerContext.set_current_user("api key bearer")

        # Debug logging
        log.debug("Received request:")
        log.debug(f"  Port: {server_port}")
        log.debug(f"  Path: {environ.get('PATH_INFO', '/')}")
        log.debug(f"  Method: {environ.get('REQUEST_METHOD', 'GET')}")

        # Set the server context based on port
        if server_port == '9000':
            server_type = 'management'
        else:
            server_type = 'core'

        config.ServerContext.set_current_server(server_type)

        response_server = None
        if server_port == '9000':
            response_server = mgmt_server
        else:
            response_server = core_server

        # Return the response from the selected server
        return response_server(environ, start_response)

    return port_router
