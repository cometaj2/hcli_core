from hcli import home
from hcli import secondaryhome
from hcli import document
from hcli import command as hcommand
from hcli import option
from hcli import execution
from hcli import finalexecution
from hcli import parameter

class HomeApi:
    def on_get(self, req, resp):
        resp.content_type = "application/hal+json"
        resp.text = home.HomeController().serialize()

class SecondaryHomeApi:
    def on_get(self, req, resp):
        resp.content_type = "application/hal+json"
        resp.text = secondaryhome.SecondaryHomeController().serialize()

class DocumentApi:
    def on_get(self, req, resp, uid):
        command = req.params['command']

        resp.content_type = "application/hal+json"
        resp.text = document.DocumentController(uid, command).serialize()

class CommandApi:
    def on_get(self, req, resp, uid):
        command = req.params['command']
        href = req.params['href']

        resp.content_type = "application/hal+json"
        resp.text = hcommand.CommandController(uid, command, href).serialize()

class OptionApi:
    def on_get(self, req, resp, uid):
        command = req.params['command']
        href = req.params['href']

        resp.content_type = "application/hal+json"
        resp.text = option.OptionController(uid, command, href).serialize()

class ParameterApi:
    def on_get(self, req, resp, uid):
        command = req.params['command']
        href = req.params['href']

        resp.content_type = "application/hal+json"
        resp.text = parameter.ParameterController(uid, command, href).serialize()

class ExecutionApi:
    def on_get(self, req, resp, uid):
        command = req.params['command']

        resp.content_type = "application/hal+json"
        resp.text = execution.ExecutionController(uid, command).serialize()

class FinalExecutionApi:
    def on_get(self, req, resp, uid):
        command = req.params['command']

        resp.content_type = "application/octet-stream"
        resp.stream = finalexecution.FinalGetExecutionController(uid, command).serialize()

    def on_post(self, req, resp, uid):
        command = req.params['command']

        resp.content_type = "application/octet-stream"
        resp.stream = finalexecution.FinalPostExecutionController(uid, command, req.stream).serialize()
