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
    uid = None
    
    def __init__(self, uid=None):
        self.href = "/hcli/cli"
        self.profile = profile.ProfileLink().href + semantic.hcli_document_type

        if uid != None:
            self.uid = uid

class DocumentController(halogen.Schema):
    route = DocumentLink().href + "/{uid}"

    self = halogen.Link(attr=lambda value: DocumentLink().href, profile=DocumentLink().profile)

    name = halogen.Attr()
    hcli_version = halogen.Attr()
    section = halogen.Attr()
