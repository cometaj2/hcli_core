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

        print(uid)
        print(req.path)
        print(req.get_param("command"))

        arg = t.findById(uid)

        serialized = document.DocumentController.serialize(document.Document(arg))
        resp.body = json.dumps(serialized)
