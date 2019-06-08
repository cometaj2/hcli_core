from haliot import hal
import urllib.parse
import template
import json
from hcli import semantic
from hcli import profile
from hcli import command as hcommand
from hcli import home
from hcli import option
from hcli import execution

class Document:
    hcli_version = None
    name = None
    section = []

    def __init__(self, document=None):
        if document != None:
            self.hcli_version = "1.0"
            self.name = document['name']
            self.section = document['section']

class DocumentLink:
    href = "/hcli/cli"
    profile = profile.ProfileLink().href + semantic.hcli_document_type
    
    def __init__(self, uid=None, command=None):
        if uid != None and command != None:
            self.href = self.href + "/" + uid + "?command=" + urllib.parse.quote(command)

class DocumentController:
    route = "/hcli/cli/{uid}"
    resource = None

    def __init__(self, uid=None, command=None):
        if uid != None and command != None:
            self.uid = uid
            self.command = command

            t = template.Template()
            arg = t.findById(self.uid)

            self.resource = hal.Resource(Document(arg))
            selflink = hal.Link(href=DocumentLink(uid, command).href)
            profilelink = hal.Link(href=DocumentLink().profile)
            homelink = hal.Link(href=home.HomeLink().href)

            self.resource.addLink("self", selflink)
            self.resource.addLink("profile", profilelink)
            self.resource.addLink("home", homelink)

            t = template.Template()
            commands = t.findCommandsForId(uid)

            if commands != None:
                for index, i in enumerate(commands):
                    com = commands[index]
                    href = com['href']
                    name = com['name']

                    newCommand = command + " " + name;

                    link = {
                               "href": hcommand.CommandLink(uid, newCommand, href).href,
                               "name": name,
                               "profile": hcommand.CommandLink().profile
                           }
                    self.resource.addLink("cli", link)

                    com = None
                    href = None
                    name = None
                    link = None

            options = t.findOptionsForId(uid);

            if options != None:
                for index, i in enumerate(options):
                    opt = options[index]
                    href = opt['href']
                    name = opt['name']

                    newCommand = command + " " + name;

                    link = {   
                               "href": option.OptionLink(uid, newCommand, href).href,
                               "name": name,
                               "profile": option.OptionLink().profile
                           }
                    self.resource.addLink("cli", link)

                    opt = None
                    href = None
                    name = None
                    link = None

 #
  #           Parameter parameter = t.findParameterForId(id);
 #
  #           if(parameter != null)
   #          {
    #                 String href = parameter.getHref();
 #
  #                   Link cli = linkTo(methodOn(HCLIParameterController.class).parameter(id, command, href)).withRel("cli").expand(href, command, href);
 #
  #                   resource.withLink(cli.getRel(), cli.getHref(), null, null, null, profile.getHref() + SemanticTypes.PARAMETER);
 #
  #                   parameter = null;
   #                  href = null;
    #                 cli = null;
     #        }

            executable = t.findExecutable(command);
 
            if executable != None:
                link = {
                           "href": execution.ExecutionLink(uid, command).href,
                           "profile": execution.ExecutionLink().profile
                       }
                self.resource.addLink("cli", link)

    def serialize(self):
        return self.resource.toHALJSON()
