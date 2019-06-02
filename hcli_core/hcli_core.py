from __future__ import absolute_import, division, print_function

import falcon
import json
import halogen
from hcli import api
from hcli import home
from hcli import document

server = falcon.API()
server.add_route(home.HomeController().route, api.HomeApi())
server.add_route(document.DocumentController().route, api.DocumentApi())
