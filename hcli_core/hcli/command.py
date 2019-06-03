import template
import json
import urllib.parse
from haliot import hal
from hcli import semantic
from hcli import profile
from hcli import document

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
    resource = None

    def __init__(self, uid=None, command=None, href=None):
        if uid != None and command != None and href != None:
            t = template.Template()
            arg = t.findById(uid);
            com = t.findCommandForId(uid, href)
            name = com['name']
           
            self.resource = hal.Resource(Command(com))
            selflink = hal.Link(href=CommandLink(uid, command, href).href)
            profilelink = hal.Link(href=CommandLink().profile)
            clilink = hal.Link(href=document.DocumentLink(href, command).href)
            homelink = hal.Link(href=home.HomeLink().href)

            self.resource.addLink("self", selflink)
            self.resource.addLink("profile", profilelink)
            self.resource.addLink("cli", clilink)
            self.resource.addLink("home", homelink)
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


    def serialize(self):
        return self.resource.toHALJSON()
