import os
import inspect

from hcli_core import logger
from hcli_core import hcliapp

log = logger.Logger("hcli_core")
log.setLevel(logger.INFO)


def connector(plugin_path=None, config_path=None):

    # Initialize core application
    log.info(f"Core application:")
    log.info(f"{plugin_path}")
    coreapp = hcliapp.HCLIApp("core", plugin_path, config_path)
    core_server = coreapp.server()

    # Initialize management application
    root = os.path.dirname(inspect.getfile(lambda: None))
    mgmt_plugin_path = os.path.join(root, 'auth', 'cli')
    log.info(f"Management application:")
    log.info(f"{mgmt_plugin_path}")
    mgmtapp = hcliapp.HCLIApp("management", mgmt_plugin_path, config_path)
    mgmt_server = mgmtapp.server()

    # We select a response server based on port
    def port_router(environ, start_response):
        server_port = environ.get('SERVER_PORT')

        # Debug logging
        log.debug("Received request:")
        log.debug(f"  Port: {server_port}")
        log.debug(f"  Path: {environ.get('PATH_INFO', '/')}")
        log.debug(f"  Method: {environ.get('REQUEST_METHOD', 'GET')}")

        # Set the server context based on port
        server_type = 'management' if server_port == '9000' else 'core'
        config.ServerContext.set_current_server(server_type)

        response_server = None
        if server_port == '9000':
            log.debug("Routing to management server with instance: {id(mgmt_server)}")
            response_server = mgmt_server
        else:
            log.debug("Routing to core server with instance: {id(core_server)}")
            response_server = core_server

        # Return the response from the selected server
        return response_server(environ, start_response)

    return port_router
