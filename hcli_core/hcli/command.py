import halogen
import template
from hcli import semantic
from hcli import profile

class Command:
    hcli_version = "1.0"
    name = None
    description = None

    def __init__(self, command=None):
        if command != None:
            self.name = command['name']
            self.description = command['description']

class CommandLink:
    href = "/hcli/cli/__cdef"
    profile = profile.ProfileLink().href + semantic.hcli_command_type
    
    def __init__(self, uid=None, command=None, href=None):
        if uid != None and command != None:
            self.href = self.href + "/" + uid + "?command=" + command + "&href=" + href

class CommandController:
    route = "/hcli/cli/__cdef/{uid}"
    schema = None
    uid = None
    command = None

    def __init__(self, uid=None, command=None, href=None):
        if uid != None and command != None:
            self.uid = uid
            self.command = command
            
            class CommandSchema(halogen.Schema):
                self = halogen.Link(attr=lambda value: CommandLink(uid, command, href).href,
                                    profile=CommandLink().profile)

                name = halogen.Attr()
                hcli_version = halogen.Attr()
                description = halogen.Attr()

#        Template t = new Template();
#        Argument arg = t.findById(id);
#        
#        Command com = t.findCommandForId(id, href);
#        String name = com.getName();
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
        t = template.Template()
        arg = t.findById(self.uid)

        return self.schema.serialize(Command(arg))
