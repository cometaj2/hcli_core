import json
import urllib

from hcli_core.haliot import hal
from hcli_core import config

from hcli_core.hcli import semantic
from hcli_core.hcli import profile
from hcli_core.hcli import command as hcommand
from hcli_core.hcli import secondaryhome
from hcli_core.hcli import option
from hcli_core.hcli import execution
from hcli_core.hcli import parameter

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
    href = secondaryhome.SecondaryHomeLink().href
    profile = profile.ProfileLink().href + semantic.hcli_document_type

    def __init__(self, uid=None, command=None, withparam=None):
        if uid != None and command != None and withparam == None:
            self.href = self.href + "/" + uid + "?command=" + urllib.parse.quote(command)
            return
        if uid != None and command != None and withparam == True:
            self.href = self.href + "/" + uid + "?command=" + command
            return

class DocumentController:
    route = secondaryhome.SecondaryHomeLink().href + "/{uid}"
    resource = None

    def __init__(self, uid=None, command=None):
        if uid != None and command != None:
            cfg = config.Config()
            t = cfg.template
            arg = t.findById(uid)

            self.resource = hal.Resource(Document(arg))
            selflink = hal.Link(href=DocumentLink(uid, command).href)
            profilelink = hal.Link(href=DocumentLink().profile)
            homelink = hal.Link(href=secondaryhome.SecondaryHomeLink().href)

            self.resource.addLink("self", selflink)
            self.resource.addLink("profile", profilelink)
            self.resource.addLink("home", homelink)

            commands = t.findCommandsForId(uid)
            if commands != None:
                for index, i in enumerate(commands):
                    com = commands[index]
                    href = com['href']
                    name = com['name']

                    newCommand = command + " " + name;

                    clilink = hal.Link(href=hcommand.CommandLink(uid, newCommand, href).href,
                                       name=name,
                                       profile=hcommand.CommandLink().profile)
                    self.resource.addLink("cli", clilink)

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

                    clilink = hal.Link(href=option.OptionLink(uid, newCommand, href).href,
                                       name=name,
                                       profile=option.OptionLink().profile)
                    self.resource.addLink("cli", clilink)

                    opt = None
                    href = None
                    name = None
                    link = None

            if(t.displayParameter(command)):
                param = t.findParameterForId(uid)
                if param != None:
                    href = param['href']

                    clilink = hal.Link(href=parameter.ParameterLink(uid, command, href).href,
                                       profile=parameter.ParameterLink().profile)

                    self.resource.addLink("cli", clilink)

                    param = None
                    href = None
                    cli = None

            executable = t.findExecutable(command);
            if executable != None:
                clilink = hal.Link(href=execution.ExecutionLink(uid, command).href,
                                   profile=execution.ExecutionLink().profile)
                self.resource.addLink("cli", clilink)


    def serialize(self):
        return self.resource.serialize()
