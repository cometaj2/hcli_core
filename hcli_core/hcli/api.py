import halogen
import template
import json
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

class CommandApi:
    def on_get(self, req, resp, uid):
        t = template.Template()
        command = req.params['command']
        href = req.params['href']
        com = t.findCommandForId(uid, href)

        serialized = document.DocumentController(uid, command, href).serialize()
        resp.body = json.dumps(serialized)
