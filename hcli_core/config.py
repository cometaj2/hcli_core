import sys
import os
import importlib
import inspect
from configparser import ConfigParser
from threading import Lock
from hcli_core import logger
import signal
import atexit

log = logger.Logger("hcli_core")


class ServerContext:
    _context = {}
    _lock = Lock()

    @classmethod
    def set_current_server(cls, server_type):
        with cls._lock:
            cls._context['current_server'] = server_type

    @classmethod
    def get_current_server(cls):
        with cls._lock:
            return cls._context.get('current_server', 'core')

class Config:
    _instances = {}  # Dictionary to store named instances
    _instance_locks = {}  # Dictionary to store locks for each named instance
    _global_lock = Lock()  # Lock for managing instance creation

    def __new__(cls, name=None):
        # If no name provided, get it from context
        if name is None:
            name = ServerContext.get_current_server()

        # Create lock for this instance name if it doesn't exist
        with cls._global_lock:
            if name not in cls._instance_locks:
                cls._instance_locks[name] = Lock()

        # Check if instance exists, if not create it
        if name not in cls._instances:
            with cls._instance_locks[name]:  # Thread-safe instance creation
                if name not in cls._instances:  # Double-checked locking
                    instance = super(Config, cls).__new__(cls)
                    # Initialize instance attributes
                    instance.name = name
                    instance.root = os.path.dirname(inspect.getfile(lambda: None))
                    instance.sample = instance.root + "/sample"
                    instance.hcli_core_manpage_path = instance.root + "/data/hcli_core.1"
                    instance.template = None
                    instance.plugin_path = instance.root + "/cli"
                    instance.cli = None
                    instance.default_config_file_path = instance.root + "/auth/credentials"
                    instance.config_file_path = None
                    instance.auth = False
                    instance.log = logger.Logger(f"hcli_core.{name}")
                    cls._instances[name] = instance

        return cls._instances[name]

    @classmethod
    def get_instance(cls, name="core"):
        """Get a named instance of the Config class."""
        return cls(name)

    @classmethod
    def list_instances(cls):
        """List all created configuration instances."""
        return list(cls._instances.keys())

    def set_config_path(self, config_path):
        if config_path:
            self.config_file_path = config_path
            self.log.info(f"Setting custom configuration for instance '{self.name}'")
        else:
            self.config_file_path = self.default_config_file_path
            self.log.warning(f"Setting default configuration for instance '{self.name}'")
        self.log.info(self.config_file_path)

    def parse_template(self, t):
        self.template = t

    def set_plugin_path(self, p):
        if p is not None:
            self.plugin_path = p
        sys.path.insert(0, self.plugin_path)
        self.cli = importlib.import_module("cli", self.plugin_path)

    def __str__(self):
        return f"Config(name='{self.name}')"
