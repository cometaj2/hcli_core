import json
import sys
import urllib
import shlex

from hcli_core import config

from hcli_core.haliot import hal
from hcli_core.hcli import semantic
from hcli_core.hcli import profile
from hcli_core.hcli import document
from hcli_core.hcli import secondaryhome


class FinalGetExecutionLink:
    href = secondaryhome.SecondaryHomeLink().href + "/exec/getexecute"
    profile = profile.ProfileLink().href + semantic.hcli_execution_type

    def __init__(self, uid=None, command=None):
        if uid != None and command != None:
            self.href = self.href + "/" + uid + "?command=" + urllib.parse.quote(command)

class FinalPostExecutionLink:
    href = secondaryhome.SecondaryHomeLink().href + "/exec/postexecute"
    profile = profile.ProfileLink().href + semantic.hcli_execution_type

    def __init__(self, uid=None, command=None):
        if uid !=None and command != None:
            self.href = self.href + "/" + uid + "?command=" + urllib.parse.quote(command)

class FinalGetExecutionController:
    route = secondaryhome.SecondaryHomeLink().href + "/exec/getexecute/{uid}"
    resource = None

    def __init__(self, uid=None, command=None):
        if uid is not None and command is not None:
            unquoted = urllib.parse.unquote(command)
            commands = unquoted.split()
            cfg = config.Config()
            CLI = cfg.cli  # This should be the CLI class itself
            self.resource = CLI(commands, None)

    def serialize(self):
        result = self.resource.execute()
        return result

class FinalPostExecutionController:
    route = secondaryhome.SecondaryHomeLink().href + "/exec/postexecute/{uid}"
    resource = None

    def __init__(self, uid=None, command=None, inputstream=None):
        if uid is not None and command is not None:
            unquoted = urllib.parse.unquote(command)
            commands = shlex.split(unquoted)
            cfg = config.Config()
            CLI = cfg.cli  # This should be the CLI class itself
            self.resource = CLI(commands, inputstream)

    def serialize(self):
        result = self.resource.execute()
        return result
