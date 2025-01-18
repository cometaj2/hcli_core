import json
import urllib
import re

from hcli_core import config

class Template:
    hcliTemplateVersion = "1.0"
    executable = []
    cli = []

    """ We load the template.json and populate available commands, executables directives and the template version """
    def __init__(self, name):
        cfg = config.Config(name)

        try:
            with open(cfg.plugin_path + "/template.json", "r") as read_file:
                data = json.load(read_file)	

            self.hcliTemplateVersion = data['hcliTemplateVersion']
            self.executable = data['executable']
            self.cli = data['cli']
        except:
            None

    """ We attempt to retrieves a specific command, identified by href, for a given command (uid) """
    def findCommandForId(self, uid, href):
        for index, i in enumerate(self.cli):
            arg = self.cli[index]
            if arg['id'] == uid:
                commands = arg['command']

                for index, j in enumerate(commands):
                    command = commands[index]
                    if command['href'] == href:
                        return command

        return None

    """ We attempt to find the command identified by uid """
    def findById(self, uid):
        for index, i in enumerate(self.cli):
            arg = self.cli[index]
            if arg['id'] == uid:
                return arg

        return None

    def findRoot(self):
        return self.cli[0]

    """ We try to see if this template owns this path structure """
    def owns(self, path):
        segments = [s for s in path.split('/') if s]

        if segments:
            uid = segments[-1]
            root = self.findRoot()
            return uid.startswith(root['id'])

        return False

    def findCommandsForId(self, uid):
        for index, i in enumerate(self.cli):
            arg = self.cli[index]
            if arg['id'] == uid:
                if 'command' in arg:
                    return arg['command']

        return None

    def findOptionsForId(self, uid):
        for index, i in enumerate(self.cli):
            arg = self.cli[index]
            if arg['id'] == uid:
                if 'option' in arg:
                    return arg['option']

        return None

    def findParameterForId(self, uid):
        for index, i in enumerate(self.cli):
            arg = self.cli[index]
            if arg['id'] == uid:
                if 'parameter' in arg:
                    return arg['parameter']

        return None

    """ We attempt to retrieves a specific option, identified by href, for a given command (uid) """
    def findOptionForId(self, uid, href):
        for index, i in enumerate(self.cli):
            arg = self.cli[index]
            if arg['id'] == uid:
                options = arg['option']

                for index, j in enumerate(options):
                    option = options[index]
                    if option['href'] == href:
                        return option

    """ We attempt to retrieves a specific executable, identified by a command line sequence"""
    def findExecutable(self, command):
        for index, i in enumerate(self.executable):
            ex = self.executable[index]
            command = urllib.parse.unquote(command)
            command = re.sub(r'\'.*?\'', '{p}', command)
            command = re.sub(r'\".*?\"', '{p}', command)
            if(ex['command'] == command):
                return ex

        return None

    """ We attempt to retrieves a specific executable command's allowed roles"""
    def findPermissionForExecutable(self, command):

        # Find the executable command definition
        executable = self.findExecutable(command)

        if not executable:
            return None

        # Return permissions if defined, None otherwise
        return executable.get('permissions')

    # We convert the current command to an executable-like format
    def displayParameter(self, command):
        for index, i in enumerate(self.executable):
            ex = self.executable[index]
            command = urllib.parse.unquote(command)
            command = re.sub(r'\'.*?\'', '{p}', command)
            command = re.sub(r'\".*?\"', '{p}', command)
            replaced = ex['command'].replace(command, '').lstrip()
            if(replaced.find('{p}') == 0):
                return True

        return False
