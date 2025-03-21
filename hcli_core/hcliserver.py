import os
import inspect
import falcon
from threading import RLock

from hcli_core.hcli import api
from hcli_core.hcli import root
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
from hcli_core.handler import HCLIErrorHandler
from hcli_problem_details import ProblemDetail

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

        server = None

        # We setup the HCLI Connector with the selective authentication for final execution only
        if self.name == 'management':
            server = falcon.App(middleware=[authenticator.SelectiveAuthenticationMiddleware(self.name),
                                            authenticator.SelectiveAuthorizationMiddleware(self.name)])
        else:
            server = falcon.App(middleware=[authenticator.SelectiveAuthenticationMiddleware(self.name)])

        # Register the HCLI error handler
        error_handler = HCLIErrorHandler()
        server.add_error_handler(falcon.HTTPError, error_handler)
        server.add_error_handler(ProblemDetail, error_handler)

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
                self.apps = {}     # type -> HCLIApp mapping
                self.server_lock = RLock()

                # Only get mgmt port from config, core port will be discovered
                self.mgmt_port = config.Config.get_management_port(config_path)
                self.core_root = config.Config.get_core_root(config_path)

                log.info(f"Lazy initialization...")
                self._initialized = True

    def _get_mgmt_app(self):
        if 'management' not in self.apps:
            root_path = os.path.dirname(inspect.getfile(lambda: None))
            mgmt_plugin_path = os.path.join(root_path, 'auth', 'cli')
            log.info("================================================")
            log.info(f"Initializing Management HCLI application:")
            log.info(f"{mgmt_plugin_path}")
            self.apps['management'] = HCLIApp("management", mgmt_plugin_path, self.config_path)
        return self.apps['management']

    def _get_core_app(self):
        if 'core' not in self.apps:
            log.info("================================================")
            log.info(f"Initializing Core HCLI application:")
            log.info(f"{self.plugin_path}")
            self.apps['core'] = HCLIApp("core", self.plugin_path, self.config_path)
        return self.apps['core']

    # Lazy initialize server for given port if it matches configuration.
    def get_server(self, port):
        if port in self.servers:
            return self.servers[port]

        with self.server_lock:
            # Check again in case another thread initialized while we waited
            if port in self.servers:
                return self.servers[port]

            # For management port, only initialize if it matches configured port or if we're aggregating the root
            if (self.mgmt_port and port == self.mgmt_port):
                mgmtapp = self._get_mgmt_app()
                server = mgmtapp.server()
                server.add_route(root.RootController.route, api.RootApi())
                self.servers[port] = ('management', server)

            # For any other port, assume it's a core server port
            elif not self.mgmt_port or port != self.mgmt_port:
                coreapp = self._get_core_app()
                server = coreapp.server()
                server.add_route(root.RootController.route, api.RootApi())
                self.servers[port] = ('core', server)

            return self.servers.get(port)

    # Special case for root aggregation.
    def get_root(self, port):
        server_info = self.get_server(port)
        if not server_info:
            return None

        server_type, server = server_info
        templates = []

        if server_type == 'management' or self.core_root == 'management':
            templates.append(self._get_mgmt_app().cfg.template)
        else:  # Core server
            templates.append(self._get_core_app().cfg.template)
            if self.core_root == 'aggregate':
                templates.append(self._get_mgmt_app().cfg.template)

        server.add_route(root.RootController.route, api.RootApi(templates))

        return server_info

    # Get appropriate server based on port and path
    def get_server_for_request(self, port, path):

        # For root path in aggregate mode, or management override over the core hcli, handle specially
        if path == '/':
            return self.get_root(port)

        server_info = self.get_server(port)
        if not server_info:
            return None

        server_type, server = server_info

        # In aggregate mode on core port or in management mode on core port
        if self.core_root == 'management':
            mgmtapp = self._get_mgmt_app()
            server = mgmtapp.server()
            return ('management', server)
        elif self.core_root == 'aggregate' and port != self.mgmt_port:
            mgmtapp = self._get_mgmt_app()

            # If path belongs to HCO, return management server
            if mgmtapp.cfg.template.owns(path):
                mgmt_server = mgmtapp.server()
                return ('management', mgmt_server)

        return server_info
