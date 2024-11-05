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


# we protect initialization but setting of the configuration, or the plugin and template parsing are run once
# at connector creation
class Config:
    _instance = None
    _instance_lock = Lock()  # Lock for singleton creation

    def __new__(cls):
        if cls._instance is None:
            with cls._instance_lock:  # Thread-safe singleton creation
                if cls._instance is None:  # Double-checked locking
                    cls._instance = super(Config, cls).__new__(cls)

                    instance = cls._instance
                    instance.root = os.path.dirname(inspect.getfile(lambda: None))
                    instance.sample = instance.root + "/sample"
                    instance.hcli_core_manpage_path = instance.root + "/data/hcli_core.1"
                    instance.template = None
                    instance.plugin_path = instance.root + "/cli"
                    instance.cli = None
                    instance.default_config_file_path = instance.root + "/auth/credentials"
                    instance.config_file_path = None
                    instance.auth = False
                    instance.log = logger.Logger("hcli_core")
        return cls._instance

    def set_config_path(self, config_path):
        if config_path:
            self.config_file_path = config_path
            self.log.info("Setting custom configuration")
        else:
            self.config_file_path = self.default_config_file_path
            self.log.info("Setting default configuration")
        self.log.info(self.config_file_path)

    def parse_template(self, t):
        self.template = t

    def set_plugin_path(self, p):
        if p is not None:
            self.plugin_path = p
        sys.path.insert(0, self.plugin_path)
        self.cli = importlib.import_module("cli", self.plugin_path)
