import json
import urllib

from hcli_core import config

from hcli_core.haliot import hal
from hcli_core.hcli import semantic
from hcli_core.hcli import profile
from hcli_core.hcli import document
from hcli_core.hcli import secondaryhome

class Command:
    hcli_version = None
    name = None
    description = None

    def __init__(self, command=None):
        if command != None:
            self.hcli_version = "1.0"
            self.name = command['name']
            self.description = command['description']

class CommandLink:
    href = secondaryhome.SecondaryHomeLink().href + "/__cdef"
    profile = profile.ProfileLink().href + semantic.hcli_command_type

    def __init__(self, uid=None, command=None, href=None):
        if uid != None and command != None and href != None:
            self.href = self.href + "/" + uid + "?command=" + urllib.parse.quote(command) + "&href=" + href

class CommandController:
    route = secondaryhome.SecondaryHomeLink().href + "/__cdef/{uid}"
    resource = None

    def __init__(self, uid=None, command=None, href=None):
        if uid != None and command != None and href != None:
            cfg = config.Config()
            t = cfg.template
            com = t.findCommandForId(uid, href)
            name = com['name']

            self.resource = hal.Resource(Command(com))
            selflink = hal.Link(href=CommandLink(uid, command, href).href)
            profilelink = hal.Link(href=CommandLink().profile)
            clilink = hal.Link(href=document.DocumentLink(href, command).href,
                               name=name,
                               profile=document.DocumentLink().profile)
            homelink = hal.Link(href=secondaryhome.SecondaryHomeLink().href)

            self.resource.addLink("self", selflink)
            self.resource.addLink("profile", profilelink)
            self.resource.addLink("cli", clilink)
            self.resource.addLink("home", homelink)

    def serialize(self):
        return self.resource.serialize()
