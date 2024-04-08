from __future__ import absolute_import, division, print_function

import json
import sys
import urllib
import shlex

from hcli_core import config

from hcli_core.haliot import hal
from hcli_core.hcli import semantic
from hcli_core.hcli import profile
from hcli_core.hcli import document
from hcli_core.hcli import home
from hcli_core.hcli import secondaryhome

class FinalGetExecutionLink:
    href = secondaryhome.SecondaryHomeLink().href + "/exec/getexecute"
    profile = profile.ProfileLink().href + semantic.hcli_execution_type

    def __init__(self, uid=None, command=None):
        if uid != None and command != None:
            self.href = self.href + "/" + uid + "?command=" + urllib.parse.quote(command)

class FinalGetExecutionController:
    route = secondaryhome.SecondaryHomeLink().href + "/exec/getexecute/{uid}"
    resource = None

    def __init__(self, uid=None, command=None):
        if uid != None and command != None:
            unquoted = urllib.parse.unquote(command)
            commands = unquoted.split()
            self.resource = config.cli.CLI(commands, None)

    def serialize(self):
        return self.resource.execute()

class FinalPostExecutionLink:
    href = secondaryhome.SecondaryHomeLink().href + "/exec/postexecute"
    profile = profile.ProfileLink().href + semantic.hcli_execution_type

    def __init__(self, uid=None, command=None):
        if uid !=None and command != None:
            self.href = self.href + "/" + uid + "?command=" + urllib.parse.quote(command)

class FinalPostExecutionController:
    route = secondaryhome.SecondaryHomeLink().href + "/exec/postexecute/{uid}"
    resource = None

    def __init__(self, uid=None, command=None, inputstream=None):
        if uid != None and command != None:
            unquoted = urllib.parse.unquote(command)
            commands = shlex.split(unquoted)
            self.resource = config.cli.CLI(commands, inputstream)

    def serialize(self):
        return self.resource.execute()
