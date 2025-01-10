import json
import urllib

from hcli_core import config

from hcli_core.haliot import hal
from hcli_core.hcli import semantic
from hcli_core.hcli import profile
from hcli_core.hcli import document
from hcli_core.hcli import secondaryhome

class Parameter:
    hcli_version = None

    def __init__(self):
        self.hcli_version = "1.0"

class ParameterLink:
    href = secondaryhome.SecondaryHomeLink().href + "/__pdef"
    profile = profile.ProfileLink().href + semantic.hcli_parameter_type

    def __init__(self, uid=None, command=None, href=None):
        if uid != None and command != None and href != None:
            self.href = self.href + "/" + uid + "?command=" + urllib.parse.quote(command) + "&href=" + href

class ParameterController:
    route = secondaryhome.SecondaryHomeLink().href + "/__pdef/{uid}"
    resource = None

    def __init__(self, uid=None, command=None, href=None):
        if uid != None and command != None and href != None:
            cfg = config.Config()
            t = cfg.template
            arg = t.findById(uid);
            param = t.findParameterForId(uid)
            name = arg['name']

            self.resource = hal.Resource(Parameter())
            selflink = hal.Link(href=ParameterLink(uid, command, href).href)
            profilelink = hal.Link(href=ParameterLink().profile)
            clilink = hal.Link(href=document.DocumentLink(uid, urllib.parse.quote(command + " ") + "{hcli_param}", withparam=True).href,
                               name=name,
                               profile=document.DocumentLink().profile,
                               templated=True)
            homelink = hal.Link(href=secondaryhome.SecondaryHomeLink().href)

            self.resource.addLink("self", selflink)
            self.resource.addLink("profile", profilelink)
            self.resource.addLink("cli", clilink)
            self.resource.addLink("home", homelink)

    def serialize(self):
        return self.resource.serialize()
