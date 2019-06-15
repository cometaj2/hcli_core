from subprocess import call

import sys

from . import package
from . import config
from . import hutils

def main():
    if len(sys.argv) == 2:

        if sys.argv[1] == "--version":
            show_dependencies()

    
        elif sys.argv[1] == "help":
            display_man_page(config.hcli_core_manpage_path)
            sys.exit(0)

        else:
            hcli_core_help()

    else:
        hcli_core_help()

# show huckle's version and the version of its dependencies
def show_dependencies():
    dependencies = ""
    for i, x in enumerate(package.dependencies):
        dependencies += " "
        dependencies += package.dependencies[i].rsplit('==', 1)[0] + "/"
        dependencies += package.dependencies[i].rsplit('==', 1)[1]
    print("hcli_core/" + package.__version__ + dependencies)

def hcli_core_help():
    hutils.eprint("for help, use:\n")
    hutils.eprint("  hcli_core help")
    sys.exit(2)

# displays a man page (file) located on a given path
def display_man_page(path):
    call(["man", path])
