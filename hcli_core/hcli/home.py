import halogen
import template
from hcli import document
from hcli import profile

class Home(object):
    None

class HomeController(halogen.Schema):
    route = "/hcli"
    href = "/hcli"

    self = halogen.Link(attr=lambda value: HomeController.href)

    t = template.Template()

    if t and t.cli and t.hcliTemplateVersion and t.hcliTemplateVersion == "1.0":
        root = t.findRoot()
        cid = root['id']
        command = "command=" + root['name']

        cli = halogen.Link(
                attr=lambda value: document.DocumentController.href + "/" + HomeController.cid + "?" + HomeController.command,
                profile=document.DocumentLink().profile
        )
##        cli = halogen.Link(
#            attr=lambda value: document.DocumentController.href + "/" + HomeController.cid + "?" + HomeController.command,
#            profile="profile"
#        )
