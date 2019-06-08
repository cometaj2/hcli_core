import template
import json
import urllib.parse
from haliot import hal
from hcli import semantic
from hcli import profile
from hcli import document
from hcli import home
from hcli import cli

class FinalExecutionLink:
    href = "/hcli/cli/exec/getexecute"
    profile = profile.ProfileLink().href + semantic.hcli_execution_type
    
    def __init__(self, command=None):
        if command != None:
            self.href = self.href + "?command=" + urllib.parse.quote(command)

class FinalExecutionController:
    route = "/hcli/cli/exec/getexecute"
    resource = None

    def __init__(self, command=None):
        if command != None:
            commands = command.split()
            self.resource = cli.CLI(commands, None)
            
    def serialize(self):
        return self.resource.execute()
