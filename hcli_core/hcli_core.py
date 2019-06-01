from __future__ import absolute_import, division, print_function

import falcon
import json
import halogen
import home
import hcli

def server():
    api = falcon.API()
    api.add_route(home.HomeController().href, home.HomeApi())
    api.add_route(hcli.DocumentController().href, hcli.DocumentApi())
    
    return api
