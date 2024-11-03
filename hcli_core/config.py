import sys
import os
import importlib
import inspect

from configparser import ConfigParser
from hcli_core import logger

# Common
root = os.path.dirname(inspect.getfile(lambda: None))
sample = root + "/sample"
hcli_core_manpage_path = root + "/data/hcli_core.1"

# Core CLI plugin handling
template = None
plugin_path = root + "/cli"
cli = None

# Configuration and credentials
default_config_file_path = root + "/auth/credentials"
config_file_path = None
auth = False

log = logger.Logger("hcli_core")


def set_config_path(config_path):
    global default_config_file_path
    global config_file_path

    if config_path:
        config_file_path = config_path
        log.info("Setting custom configuration")
    else:
        config_file_path = default_config_file_path
        log.info("Setting default configuration")
    log.info(config_file_path)

""" We parse the HCLI json template to load the HCLI navigation in memory """
def parse_template(t):
    global template
    template = t

""" we setup dynamic loading of the cli module to allow for independent development and loading, independent of hcli_core development """
def set_plugin_path(p):
    global plugin_path
    global cli
    if p is not None:
        plugin_path = p

    sys.path.insert(0, plugin_path)
    cli = importlib.import_module("cli", plugin_path)
