import halogen
import template
from hcli import semantic
from hcli import profile

class Document:
    hcli_version = "1.0"
    name = None
    section = []

    def __init__(self, document=None):
        if document != None:
            self.name = document['name']
            self.section = document['section']

class DocumentLink:
    uid = None
    href = "/hcli/cli"
    profile = None
    
    def __init__(self, uid=None):
        if uid != None:
            self.uid = uid
            self.href = self.href + "/" + uid 
            self.profile = profile.ProfileLink().href + semantic.hcli_document_type

class DocumentSchema(halogen.Schema):
#    self = halogen.Link(attr=lambda value: DocumentLink("jsonf").href, profile=DocumentLink().profile)

    name = halogen.Attr()
    hcli_version = halogen.Attr()
    section = halogen.Attr()

class DocumentController:
    route = "/hcli/cli/{uid}"
    schema = None

    def __init__(self, uid=None):
        if uid != None:
            self.uid = uid
            
            class DocumentSchema(halogen.Schema):
                self = halogen.Link(attr=lambda value: DocumentLink(uid).href, profile=DocumentLink().profile)

                name = halogen.Attr()
                hcli_version = halogen.Attr()
                section = halogen.Attr()

            self.schema = DocumentSchema

    def serialize(self):
        t = template.Template()
        arg = t.findById(self.uid)

        return self.schema.serialize(Document(arg))
