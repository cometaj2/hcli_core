import os
import inspect

from hcli_core import logger
from hcli_core import hcliapp
from hcli_core import config

log = logger.Logger("hcli_core")
log.setLevel(logger.INFO)


def connector(plugin_path=None, config_path=None):

    # Initialize core application
    log.info("================================================")
    log.info(f"Core HCLI application:")
    log.info(f"{plugin_path}")
    coreapp = hcliapp.HCLIApp("core", plugin_path, config_path)
    core_server = coreapp.server()

    # Initialize management application if applicable
    mgmt_port = config.Config.get_management_port(config_path)
    mgmt_server = None
    if mgmt_port is not None:
        root = os.path.dirname(inspect.getfile(lambda: None))
        mgmt_plugin_path = os.path.join(root, 'auth', 'cli')
        log.info("================================================")
        log.info(f"Management HCLI application:")
        log.info(f"{mgmt_plugin_path}")
        mgmtapp = hcliapp.HCLIApp("management", mgmt_plugin_path, config_path)
        mgmt_port = mgmtapp.port()
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

        # If using HCOAK Bearer auth, it will be in format "Bearer base64(keyid:hcoak(apikey))"
        if auth_info.startswith('Bearer '):
            import base64

            # Extract and decode the base64 credentials
            encoded_credentials = auth_info.split(' ')[1]
            decoded = base64.b64decode(encoded_credentials).decode('utf-8')
            keyid = decoded.split(':')[0]

            # Store username in environ for downstream handlers
            environ['REMOTE_USER'] = keyid
            config.ServerContext.set_current_user(keyid)

        # Debug logging
        log.debug("Received request:")
        log.debug(f"  Port: {server_port}")
        log.debug(f"  Path: {environ.get('PATH_INFO', '/')}")
        log.debug(f"  Method: {environ.get('REQUEST_METHOD', 'GET')}")

        # Route to appropriate server
        if mgmt_server and int(server_port) == mgmt_port:
            config.ServerContext.set_current_server('management')
            return mgmt_server(environ, start_response)

        config.ServerContext.set_current_server('core')
        return core_server(environ, start_response)

    return port_router
