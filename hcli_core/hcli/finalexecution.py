from __future__ import absolute_import, division, print_function

import json
import sys
import config
import urllib
import shlex
from haliot import hal
from hcli import semantic
from hcli import profile
from hcli import document
from hcli import home
from hcli import secondaryhome

class FinalGetExecutionLink:
    href = secondaryhome.SecondaryHomeLink().href + "/exec/getexecute"
    profile = profile.ProfileLink().href + semantic.hcli_execution_type
    
    def __init__(self, command=None):
        if command != None:
            self.href = self.href + "?command=" + urllib.parse.quote(command)

class FinalGetExecutionController:
    route = secondaryhome.SecondaryHomeLink().href + "/exec/getexecute"
    resource = None

    def __init__(self, command=None):
        if command != None:
            unquoted = urllib.parse.unquote(command)
            commands = unquoted.split()
            self.resource = config.cli.CLI(commands, None)
            
    def serialize(self):
        return self.resource.execute()

class FinalPostExecutionLink:
    href = secondaryhome.SecondaryHomeLink().href + "/exec/postexecute"
    profile = profile.ProfileLink().href + semantic.hcli_execution_type

    def __init__(self, command=None):
        if command != None:
            self.href = self.href + "?command=" + urllib.parse.quote(command)

class FinalPostExecutionController:
    route = secondaryhome.SecondaryHomeLink().href + "/exec/postexecute"
    resource = None

    def __init__(self, command=None, inputstream=None):
        if command != None:
            unquoted = urllib.parse.unquote(command)
            commands = shlex.split(unquoted)
            self.resource = config.cli.CLI(commands, inputstream)

    def serialize(self):
        return self.resource.execute()    
