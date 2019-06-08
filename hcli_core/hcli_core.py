from __future__ import absolute_import, division, print_function

import falcon
import json
from hcli import api
from hcli import home
from hcli import document
from hcli import command
from hcli import option
from hcli import execution
from hcli import finalexecution

server = falcon.API()
server.add_route(home.HomeController.route, api.HomeApi())
server.add_route(document.DocumentController.route, api.DocumentApi())
server.add_route(command.CommandController.route, api.CommandApi())
server.add_route(option.OptionController.route, api.OptionApi())
server.add_route(execution.ExecutionController.route, api.ExecutionApi())
server.add_route(finalexecution.FinalExecutionController.route, api.FinalExecutionApi())
