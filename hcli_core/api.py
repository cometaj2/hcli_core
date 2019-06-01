import falcon
import json
import halogen
import semantics
import template
import hcli

class HomeApi():
    def __init__(self):
        self.controller = hcli.HomeController()

    def on_get(self, req, resp):
        t = template.Template()

        serialized = hcli.HomeController.serialize(hcli.Home())
        resp.body = json.dumps(serialized)

class DocumentApi():
    def __init__(self):
        self.controller = hcli.DocumentController()

    def on_get(self, req, resp, cid):
        t = template.Template()

        print(cid)
        print(req.path)
        print(req.get_param("command"))

        arg = t.findById("jsonf")

        serialized = hcli.DocumentController.serialize(hcli.Document(arg))
        resp.body = json.dumps(serialized)
