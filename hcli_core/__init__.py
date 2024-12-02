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

        # Get or initialize the appropriate server
        server_info = server_manager.get_server(server_port)
        if not server_info:
            log.warning(f"Request received on unconfigured port: {server_port}")
            start_response('404 Not Found', [('Content-Type', 'text/plain')])
            return [b'No server configured for this port']

        server_type, server = server_info

        # Get authentication info from WSGI environ
        auth_info = environ.get('HTTP_AUTHORIZATION', '')

        # If using Basic auth, it will be in format "Basic base64(username:password)"
        if auth_info.startswith('Basic '):

            # Extract and decode the base64 credentials
            encoded_credentials = auth_info.split(' ')[1]
            decoded = base64.b64decode(encoded_credentials).decode('utf-8')
            username = decoded.split(':')[0]

            # Store username in environ for downstream handlers
            environ['REMOTE_USER'] = username
            config.ServerContext.set_current_user(username)

        # If using HCOAK Bearer auth, it will be in format "Bearer base64(keyid:hcoak(apikey))"
        if auth_info.startswith('Bearer '):

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

        # Set server context and route request
        config.ServerContext.set_current_server(server_type)
        return server(environ, start_response)

    return port_router
