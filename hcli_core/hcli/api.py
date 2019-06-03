import template
from hcli import home
from hcli import document
from hcli import command as hcommand

class HomeApi:
    def on_get(self, req, resp):
        resp.body = home.HomeController().serialize()

class DocumentApi:
    def on_get(self, req, resp, uid):
        t = template.Template()
        arg = t.findById(uid)
        command = req.params['command']

        resp.body = document.DocumentController(uid, command).serialize()

class CommandApi:
    def on_get(self, req, resp, uid):
        t = template.Template()
        command = req.params['command']
        href = req.params['href']

        resp.body = hcommand.CommandController(uid, command, href).serialize()
