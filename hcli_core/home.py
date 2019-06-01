import falcon
import json
import halogen
from . import semantics
from . import hcli
from . import template

class Home(object):
    None

class HomeController(halogen.Schema):
    href = "/hcli"
    
    self = halogen.Link(attr=lambda value: HomeController().href)

    t = template.Template()

    if t and t.cli and t.hcliTemplateVersion and t.hcliTemplateVersion == "1.0":
        root = t.findRoot()
        cid = root['id']
        command = "command=" + root['name']

        #cli = halogen.Link(
        #        attr=lambda value: hcli.DocumentController().href + "/" + HomeController.cid + "?" + HomeController.command,
        #        profile=lambda value: hcli.DocumentController().profile
        #)
        cli = halogen.Link(
            attr=lambda value: hcli.DocumentController().href + "/" + HomeController.cid + "?" + HomeController.command
        )

class HomeApi():
    def __init__(self):
        self.controller = HomeController()

    def on_get(self, req, resp) -> None:
        t = template.Template()

        serialized = HomeController.serialize(Home())
        resp.body = json.dumps(serialized)
