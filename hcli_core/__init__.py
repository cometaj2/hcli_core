from __future__ import absolute_import, division, print_function

import json
from hcli_core.hcli import api
from hcli_core.hcli import home
from hcli_core.hcli import secondaryhome
from hcli_core.hcli import document
from hcli_core.hcli import command
from hcli_core.hcli import option
from hcli_core.hcli import execution
from hcli_core.hcli import finalexecution
from hcli_core.hcli import parameter

from hcli_core import config
from hcli_core import template

def connector(plugin_path=None):
    import falcon

    # We load the HCLI template in memory to reduce disk io
    config.set_plugin_path(plugin_path)
    config.parse_template(template.Template())

    # We setup the HCLI Connector
    server = falcon.App()
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
