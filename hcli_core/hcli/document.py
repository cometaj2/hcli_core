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
    href = "/hcli/cli"
    profile = profile.ProfileLink().href + semantic.hcli_document_type
    
    def __init__(self, uid=None, command=None):
        if uid != None and command != None:
            self.href = self.href + "/" + uid + "?command=" + command

class DocumentController:
    route = "/hcli/cli/{uid}"
    schema = None
    uid = None
    command = None

    def __init__(self, uid=None, command=None):
        if uid != None and command != None:
            self.uid = uid
            self.command = command
            
            class DocumentSchema(halogen.Schema):
                self = halogen.Link(attr=lambda value: DocumentLink(uid, command).href,
                                    profile=DocumentLink().profile)

                name = halogen.Attr()
                hcli_version = halogen.Attr()
                section = halogen.Attr()

            self.schema = DocumentSchema

    def serialize(self):
        t = template.Template()
        arg = t.findById(self.uid)

        return self.schema.serialize(Document(arg))
