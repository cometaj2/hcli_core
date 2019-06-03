from __future__ import absolute_import, division, print_function

import falcon
import json
from hcli import api
from hcli import home
from hcli import document
from hcli import command

server = falcon.API()
server.add_route(home.HomeController().route, api.HomeApi())
server.add_route(document.DocumentController().route, api.DocumentApi())
server.add_route(command.CommandController().route, api.CommandApi())
