from __future__ import absolute_import, division, print_function

import falcon
import json
import halogen
from . import home
from . import hcli

def server():
    api = falcon.API()
    api.add_route(home.HomeController().href, home.HomeApi())
    api.add_route(hcli.DocumentController().href, hcli.DocumentApi())
    
    return api
