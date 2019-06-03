import halogen
import template
import urllib.parse
from hcli import semantic
from hcli import profile

class Command:
    hcli_version = None
    name = None
    description = None

    def __init__(self, command=None):
        if command != None:
            hcli_version = "1.0"
            self.name = command['name']
            self.description = command['description']

class CommandLink:
    href = "http://127.0.0.1:8000/hcli/cli/__cdef"
    profile = profile.ProfileLink().href + semantic.hcli_command_type
    
    def __init__(self, uid=None, command=None, href=None):
        if uid != None and command != None and href != None:
            self.href = self.href + "/" + uid + "?command=" + urllib.parse.quote(command) + "&href=" + href

class CommandController:
    route = "/hcli/cli/__cdef/{uid}"
    schema = None
    uid = None
    command = None
    href = None
    com = None

    def __init__(self, uid=None, command=None, href=None):
        if uid != None and command != None and href != None:
            self.uid = uid
            self.command = command
            self.href = href

            t = template.Template()
            arg = t.findById(uid);
            self.com = t.findCommandForId(uid, href)
            name = self.com['name']
            
            class CommandSchema(halogen.Schema):
                self = halogen.Link(attr=lambda value: CommandLink(uid, command, href).href)
                profile = halogen.Link(CommandLink().profile)

                name = halogen.Attr()
                hcli_version = halogen.Attr()
                description = halogen.Attr()


#        
#        Representation resource = (new HCLICommand(com)).toResource();
#        
#        Link self = linkTo(methodOn(HCLICommandController.class).command(id, command, href)).withSelfRel().expand(id, command, href);
#        Link home = linkTo(methodOn(HomeController.class).home()).withRel("home");
#        Link profile = linkTo(methodOn(ProfileController.class).profile()).withRel("profile");
#        Link cli = linkTo(methodOn(HCLIDocumentController.class).cli(href, command)).withRel("cli").expand(href, command);
#        
#        resource.withLink(self.getRel(), self.getHref())
#                .withLink(home.getRel(), home.getHref())
#                .withLink(profile.getRel(), profile.getHref() + SemanticTypes.COMMAND)
#                .withLink(cli.getRel(), cli.getHref(), name, null, null, profile.getHref() + SemanticTypes.HCLI_DOCUMENT);

            self.schema = CommandSchema

    def serialize(self):
        return self.schema.serialize(Command(self.com))
