from __future__ import absolute_import, division, print_function

import falcon
import json
import halogen
import api
import hcli

def server():
    local = falcon.API()
    local.add_route(hcli.HomeController().href, api.HomeApi())
    local.add_route(hcli.DocumentController().href, api.DocumentApi())
    
    return local
