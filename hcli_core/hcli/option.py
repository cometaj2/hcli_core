import json
import urllib

from hcli_core import config

from hcli_core.haliot import hal
from hcli_core.hcli import semantic
from hcli_core.hcli import profile
from hcli_core.hcli import document
from hcli_core.hcli import secondaryhome

class Option:
    hcli_version = None
    name = None
    description = None

    def __init__(self, option=None):
        if option != None:
            self.hcli_version = "1.0"
            self.name = option['name']
            self.description = option['description']

class OptionLink:
    href = secondaryhome.SecondaryHomeLink().href + "/__odef"
    profile = profile.ProfileLink().href + semantic.hcli_option_type

    def __init__(self, uid=None, option=None, href=None):
        if uid != None and option != None and href != None:
            self.href = self.href + "/" + uid + "?command=" + urllib.parse.quote(option) + "&href=" + href

class OptionController:
    route = secondaryhome.SecondaryHomeLink().href + "/__odef/{uid}"
    resource = None

    def __init__(self, uid=None, command=None, href=None):
        if uid != None and command != None and href != None:
            cfg = config.Config()
            t = cfg.template
            arg = t.findById(uid);
            opt = t.findOptionForId(uid, href)
            name = opt['name']

            self.resource = hal.Resource(Option(opt))
            selflink = hal.Link(href=OptionLink(uid, command, href).href)
            profilelink = hal.Link(href=OptionLink().profile)
            clilink = hal.Link(href=document.DocumentLink(uid, command).href)
            homelink = hal.Link(href=secondaryhome.SecondaryHomeLink().href)

            self.resource.addLink("self", selflink)
            self.resource.addLink("profile", profilelink)
            self.resource.addLink("cli", clilink)
            self.resource.addLink("home", homelink)

    def serialize(self):
        return self.resource.serialize()
