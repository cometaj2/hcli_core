import halogen
import template
import json
from hcli import semantic
from hcli import profile
from hcli import command as hcommand

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

                t = template.Template()
                commands = t.findCommandsForId(uid)

                if commands != None:
                    clis = [];
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
                        clis.append(link)
 
                        com = None;
                        href = None;
                        name = None;
                        link = None;
                   
                    cli = halogen.Link(clis)

#
  #           List<Option> options = t.findOptionsForId(id);
 #
  #           if(options != null)
   #          {
    #             for(int i = 0; i < options.size(); i++)
     #            {
      #               Option opt = (Option) options.get(i);
       #              String href = opt.getHref();
        #             String name = opt.getName();
 #
  #                   String newCommand = command + " " + name;
 #
  #                   Link cli = linkTo(methodOn(HCLIOptionController.class).option(id, newCommand, href)).withRel("cli").expand(href, newCommand, href);
 #
  #                   resource.withLink(cli.getRel(), cli.getHref(), name, null, null, profile.getHref() + SemanticTypes.OPTION);
 #
  #                   opt = null;
   #                  href = null;
    #                 name = null;
     #                cli = null;
      #           }
       #      }
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

      #       Executable al = t.findExecutable(command);
 #
  #           if(al != null)
   #          {
    #             Link cli = linkTo(methodOn(HCLIExecutionController.class).execution(id, command)).withRel("cli").expand(id, command);
 #
  #               resource.withLink(cli.getRel(), cli.getHref(), null, null, null, profile.getHref() + SemanticTypes.EXECUTION);
   #          }

            self.schema = DocumentSchema

    def serialize(self):
        t = template.Template()
        arg = t.findById(self.uid)

        return self.schema.serialize(Document(arg))
