from hcli_core import config

from hcli_core.haliot import hal
from hcli_core.hcli import document

class SecondaryHome(object):
    None

class SecondaryHomeLink:
    href = None

    def __init__(self):
        self.href = "/hcli/cli"

class SecondaryHomeController:
    route = "/hcli/cli"
    resource = None

    def __init__(self):
        cfg = config.Config()
        t = cfg.template

        if t and t.cli and t.hcliTemplateVersion and t.hcliTemplateVersion == "1.0":
            root = t.findRoot()
            uid = root['id']
            command = root['name']

            self.resource = hal.Resource(SecondaryHome())
            selflink = hal.Link(href=SecondaryHomeLink().href)
            clilink = hal.Link(href=document.DocumentLink(uid, command).href,
                               profile=document.DocumentLink().profile)

            self.resource.addLink("self", selflink)
            self.resource.addLink("cli", clilink)

    def serialize(self):
        return self.resource.serialize()
