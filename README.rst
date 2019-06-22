HCLI Core
=========

An HCLI Connector that can be used to expose any CLI via hypertext
command line interface (HCLI) semantics.

----

HCLI Core is a WSGI application that provides a way for developers to expose a CLI via HCLI semantics
while providing dynamic and up to date in-band access to all the API/CLI documentation,
man page style, which showcases commands, options, and parameters available for execution.

Most, if not all, programming languages have a way to issue shell commands. With the help
of any generic HCLI client, such as Huckle, APIs that make use of HCLI semantics are readily consumable
anywhere via the familiar command line (CLI) mode of operation, and this, without there being a need to write
a custom and dedicated CLI to interact with a specific HCLI API.

The HCLI Internet-Draft [1] is a work in progress by the author and 
the current implementation leverages hal+json alongside a static form of ALPS
(semantic profile) [2] to help enable widespread cross media-type support.

You can find out more about HCLI on hcli.io [3]

Help shape HCLI and it's ecosystem on the discussion list [4] or by raising issues on github!

[1] https://github.com/cometaj2/I-D/tree/master/hcli

[2] http://alps.io

[3] https://hcli.io

[4] https://groups.google.com/forum/#!forum/huck-hypermedia-unified-cli-with-a-kick

Installation
------------

hcli_core requires Python 2.7, 3.4-3.6 and pip.

You'll need an WSGI compliant application server to run hcli_core. For example, you can use Green Unicorn (https://gunicorn.org/)

    $ pip install gunicorn

Download the hcli_core wherever you want it to be installed and navigate into the hcli_core folder. For example:

    $ cd /home/foma/hcli_core/hcli_core

    $ gunicorn --workers=5 --threads=2 "hcli_core:server"

Alternatively, if you install hcli_core via pip, you can launch gunicorn from anywhere by using "hcli_core path"

    $ pip install hcli_core

    $ gunicorn --workers=5 --threads=2 --chdir \`hcli_core path\` "hcli_core:server"

Bugs
----

- No good handling of control over request and response in cli code which can lead to exceptions and empty response client side.
