import os
import inspect
import falcon
from threading import RLock

from hcli_core.hcli import api
from hcli_core.hcli import home
from hcli_core.hcli import secondaryhome
from hcli_core.hcli import document
from hcli_core.hcli import command
from hcli_core.hcli import option
from hcli_core.hcli import execution
from hcli_core.hcli import finalexecution
from hcli_core.hcli import parameter

from hcli_core import logger
from hcli_core import config
from hcli_core import template

from hcli_core.auth.cli import authenticator
from hcli_core.error import handle_hcli_error, HCLIError

log = logger.Logger("hcli_core")


class HCLIApp:

    def __init__(self, name, plugin_path, config_path):
        self.name = name
        self.cfg = config.Config(name)

        # We set the configuration/credentials path for use the authentication middleware
        self.cfg.set_config_path(config_path)
        self.cfg.parse_configuration()

        # We load the HCLI template in memory to reduce disk io
        self.cfg.set_plugin_path(plugin_path)
        self.cfg.parse_template(template.Template(name))

    def server(self):

        # We setup the HCLI Connector with the selective authentication for final execution only
        server = falcon.App(middleware=[authenticator.SelectiveAuthMiddleware(self.name)])

        # Register the HCLI error handler
        server.add_error_handler(falcon.HTTPError, handle_hcli_error)
        server.add_error_handler(HCLIError, handle_hcli_error)

        server.add_route(home.HomeController.route, api.HomeApi())
        server.add_route(secondaryhome.SecondaryHomeController.route, api.SecondaryHomeApi())
        server.add_route(document.DocumentController.route, api.DocumentApi())
        server.add_route(command.CommandController.route, api.CommandApi())
        server.add_route(option.OptionController.route, api.OptionApi())
        server.add_route(execution.ExecutionController.route, api.ExecutionApi())
        server.add_route(finalexecution.FinalGetExecutionController.route, api.FinalExecutionApi())
        server.add_route(finalexecution.FinalPostExecutionController.route, api.FinalExecutionApi())
        server.add_route(parameter.ParameterController.route, api.ParameterApi())

        return server

    def port(self):
        return self.cfg.mgmt_port

class LazyServerManager:
    _instance = None
    _init_lock = RLock()

    def __new__(cls, *args, **kwargs):
        with cls._init_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, plugin_path=None, config_path=None):
        with self._init_lock:
            if not self._initialized:
                self.plugin_path = plugin_path
                self.config_path = config_path
                self.servers = {}  # port -> server mapping
                self.server_lock = RLock()

                # Only get mgmt port from config, core port will be discovered
                self.mgmt_port = config.Config.get_management_port(config_path)

                log.info(f"Waiting for first request with lazy initialization...")
                self._initialized = True

    # Lazy initialize server for given port if it matches configuration.
    def get_server(self, port):
        if port in self.servers:
            return self.servers[port]

        with self.server_lock:
            # Check again in case another thread initialized while we waited
            if port in self.servers:
                return self.servers[port]

            # For management port, only initialize if it matches configured port
            if self.mgmt_port and port == self.mgmt_port:
                root = os.path.dirname(inspect.getfile(lambda: None))
                mgmt_plugin_path = os.path.join(root, 'auth', 'cli')
                log.info("================================================")
                log.info(f"Initializing Management HCLI application:")
                log.info(f"{mgmt_plugin_path}")
                mgmtapp = HCLIApp("management", mgmt_plugin_path, self.config_path)
                self.servers[port] = ('management', mgmtapp.server())

            # For any other port, assume it's a core server port
            elif not self.mgmt_port or port != self.mgmt_port:
                log.info("================================================")
                log.info(f"Initializing Core HCLI application:")
                log.info(f"{self.plugin_path}")
                coreapp = HCLIApp("core", self.plugin_path, self.config_path)
                self.servers[port] = ('core', coreapp.server())

            return self.servers.get(port)
