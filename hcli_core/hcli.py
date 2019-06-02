import falcon
import json
import halogen
import semantic
import hcli
import template

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

#        cli = halogen.Link(
#                attr=lambda value: hcli.DocumentController().href + "/" + HomeController.cid + "?" + HomeController.command,
#                profile=lambda value: hcli.DocumentController().profile
#        )
        cli = halogen.Link(
            attr=lambda value: DocumentController.href + "/" + HomeController.cid + "?" + HomeController.command,
            profile="profile"
        )

class ProfileLink:
    href = None
    
    def __init__(self):
        self.href = "/hcli/profile"

class Document:
    hcli_version = "1.0"
    name = None
    section = []

    def __init__(self, document):
        self.name = document['name']
        self.section = document['section']

class DocumentLink:
    href = None
    profile = None
    
    def __init__(self):
        self.href = "/hcli/cli"
        self.profile = ProfileLink().href + semantic.hcli_document_type

class DocumentController(halogen.Schema):
    route = DocumentLink().href + "/{cid}"
    href = DocumentLink().href
    profile = DocumentLink().profile

    self = halogen.Link(attr=lambda value: DocumentController.href, profile=profile)

    name = halogen.Attr()
    hcli_version = halogen.Attr()
    section = halogen.Attr()
