import falcon
import json
import halogen
import template
from hcli import home
from hcli import document

class HomeApi:
    def on_get(self, req, resp):
        serialized = home.HomeController.serialize(home.Home())
        resp.body = json.dumps(serialized)

class DocumentApi:
    def on_get(self, req, resp, uid):
        t = template.Template()
        arg = t.findById(uid)
        command = req.params['command']

        serialized = document.DocumentController(uid, command).serialize()
        resp.body = json.dumps(serialized)
