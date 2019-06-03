import json

class Template:
    hcliTemplateVersion = "1.0"
    executable = []
    cli = []

    """ We load the template.json and populate available commands, executables directives and the template version """
    def __init__(self):
        
        try:
            with open("template.json", "r") as read_file:
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

    def findCommandsForId(self, uid):
        for index, i in enumerate(self.cli):
            arg = self.cli[index]
            if arg['id'] == uid:
                if 'command' in arg:
                    return arg['command']
        
        return None

#    public List<Option> findOptionsForId(String id)
#    {
#        for(int i = 0; i < this.getCLI().size(); i++)
#        {
#            Argument doc = this.getCLI().get(i);
#            if(doc.getId().equals(id))
#            {
#                return doc.getOption();
#            }
#        }
#
#        return null;
#    }

#    public Parameter findParameterForId(String id)
#    {
#        for(int i = 0; i < this.getCLI().size(); i++)
#        {
#            Argument doc = this.getCLI().get(i);
#            if(doc.getId().equals(id))
#            {
#                return doc.getParameter();
#            }
#        }
#
#        return null;
#    }

#    public Option findOptionForId(String id, String href)
#    {
#        for(int i = 0; i < this.getCLI().size(); i++)
#        {
#            Argument doc = this.getCLI().get(i);
#            if(doc.getId().equals(id))
#            {
#                List<Option> options = doc.getOption();
#
#                for(int j = 0; j < options.size(); j++)
#                {
#                    Option opt = options.get(j);
#                    if(opt.getHref().equals(href))
#                    {
#                        return opt;
#                    }
#                }
#            }
#        }
#
#        return null;
#    }

#    public Executable findExecutable(String command)
#    {
#        for(int i = 0; i < this.getExecutable().size(); i++)
#        {
#            Executable al = this.getExecutable().get(i);
#            if(al.getCommand().equals(command))
#            {
#                return al;
#            }
#        }
#
#        return null;
#    }
