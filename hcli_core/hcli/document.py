import halogen
from hcli import semantic
from hcli import profile

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
        self.profile = profile.ProfileLink().href + semantic.hcli_document_type

class DocumentController(halogen.Schema):
    route = DocumentLink().href + "/{cid}"
    href = DocumentLink().href
    profile = DocumentLink().profile

    self = halogen.Link(attr=lambda value: DocumentController.href, profile=profile)

    name = halogen.Attr()
    hcli_version = halogen.Attr()
    section = halogen.Attr()
