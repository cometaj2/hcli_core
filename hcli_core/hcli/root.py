from hcli_core import config
from hcli_core.haliot import hal
from hcli_core.hcli import document

class Root(object):
    None

class RootLink:
    href = None

    def __init__(self):
        self.href = "/"

class RootController:
    route = "/"
    resource = None

    def __init__(self, templates=None):
        if not templates:
            cfg = config.Config()
            templates = [cfg.template]

        self.resource = hal.Resource(Root())
        selflink = hal.Link(href=RootLink().href)
        self.resource.addLink("self", selflink)

        for t in templates:
            if t and t.cli and t.hcliTemplateVersion and t.hcliTemplateVersion == "1.0":
                root = t.findRoot()
                uid = root['id']
                command = root['name']
                clilink = hal.Link(href=document.DocumentLink(uid, command).href,
                                   profile=document.DocumentLink().profile)
                self.resource.addLink("cli", clilink)

    def serialize(self):
        return self.resource.serialize()
