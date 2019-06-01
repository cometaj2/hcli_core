import falcon
import json
import halogen
from . import semantics
from . import hcli
from . import template

class Document:
    hcli_version = "1.0"
    name = None
    section = []

    def __init__(self, document):
        self.name = document['name']
        self.section = document['section']

class DocumentController(halogen.Schema):
    href = "/hcli/cli/{cid}"

    self = halogen.Link(attr=lambda value: DocumentController().href)

    name = halogen.Attr()
    hcli_version = halogen.Attr()
    section = halogen.Attr()

class DocumentApi():
    def __init__(self):
        self.controller = DocumentController()

    def on_get(self, req, resp, cid) -> None:
        t = template.Template()

        print(cid)
        print(req.path)
        print(req.get_param("command"))
        
        arg = t.findById("jsonf")        

        serialized = DocumentController.serialize(Document(arg))
        resp.body = json.dumps(serialized)
