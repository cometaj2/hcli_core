from hcli_core.hcli import root
from hcli_core.hcli import secondaryhome
from hcli_core.hcli import document
from hcli_core.hcli import command as hcommand
from hcli_core.hcli import option
from hcli_core.hcli import execution
from hcli_core.hcli import finalexecution
from hcli_core.hcli import parameter

from functools import wraps

# Class decorator to mark resources that need authentication or authorization.
# This allows us to navigate the HCLI API surface without authentication except for final execution.
def requires_auth(cls):
    cls.requires_authentication = True
    cls.requires_authorization = True
    return cls

class RootApi:
    def __init__(self, templates=None):
        self.templates = templates

    def on_get(self, req, resp):
        resp.content_type = "application/hal+json"
        resp.text = root.RootController(self.templates).serialize()

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

@requires_auth
class FinalExecutionApi:
    def on_get(self, req, resp, uid):
        command = req.params['command']

        resp.content_type = "application/octet-stream"
        resp.stream = finalexecution.FinalGetExecutionController(uid, command).serialize()

    def on_post(self, req, resp, uid):
        command = req.params['command']

        resp.content_type = "application/octet-stream"
        resp.stream = finalexecution.FinalPostExecutionController(uid, command, req.stream).serialize()
