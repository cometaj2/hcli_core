import sys
import os
import importlib
import inspect

from configparser import ConfigParser
from hcli_core import logger

root = os.path.dirname(inspect.getfile(lambda: None))
sample = root + "/sample"
hcli_core_manpage_path = root + "/data/hcli_core.1"
template = None
plugin_path = root + "/cli"
default_config_file_path = root + "/hcli_core.config"
config_file_path = None
cli = None

log = logger.Logger("hcli_core")


# parses the configuration of a given cli to set configured execution
def parse_configuration(config_path):
    global default_config_file_path
    global config_file_path
    global auth

    if config_path:
        config_file_path = config_path
        log.info("Loading custom configuration")
    else:
        config_file_path = default_config_file_path
        log.info("Loading default configuration")
    log.info(config_file_path)

    try:
        parser = ConfigParser()
        parser.read(config_file_path)
        if parser.has_section("default"):
            for section_name in parser.sections():
                log.debug("[" + section_name + "]")
                for name, value in parser.items("default"):
                    if name == "auth":
                        auth = value
                        log.debug(name + " = " + auth)
        else:
            sys.exit("No default configuration available for " + config_file_path) 
    except:
        sys.exit("Unable to load configuration.") 


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
