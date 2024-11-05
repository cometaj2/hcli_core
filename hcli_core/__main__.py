from subprocess import call

import sys

from hcli_core import package
from hcli_core import config
from hcli_core import hutils

cfg = config.Config()


def main():
    if len(sys.argv) == 2:

        if sys.argv[1] == "--version":
            show_dependencies()
            sys.exit(0)

        elif sys.argv[1] == "help":
            display_man_page(cfg.hcli_core_manpage_path)
            sys.exit(0)

        elif sys.argv[1] == "path":
            print(cfg.root)
            sys.exit(0)

        else:
            hcli_core_help()

    elif len(sys.argv) == 3:

        if sys.argv[1] == "sample":
            if sys.argv[2] == "hub":
                print(cfg.sample + "/hub/cli")
            elif sys.argv[2] == "hfm":
                print(cfg.sample + "/hfm/cli")
            elif sys.argv[2] == "nw":
                print(cfg.sample + "/nw/cli")
            elif sys.argv[2] == "hptt":
                print(cfg.sample + "/hptt/cli")

            sys.exit(0)

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
