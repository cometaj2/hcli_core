HCLI Core |build status|_ |pypi|_
=================================

An HCLI Connector that can be used to expose any CLI via hypertext
command line interface (HCLI) semantics.

----

HCLI Core implements the Service Connector pattern as a WSGI application and provides a way for developers to
expose a CLI via HCLI semantics which yields dynamic and up to date in-band access to man page style API/CLI documentation.

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

hcli_core requires Python 3.5-3.7 and pip.

You'll need an WSGI compliant application server to run hcli_core. For example, you can use Green Unicorn (https://gunicorn.org/)

    $ pip install gunicorn

Download the hcli_core wherever you want it to be installed and navigate into the hcli_core folder. For example:

    $ cd /home/foma/hcli_core/hcli_core

    $ gunicorn --workers=5 --threads=2 "hcli_core:HCLI().connector"

Alternatively, if you install hcli_core via pip, you can launch gunicorn from anywhere by using "hcli_core path". You can also look at the hcli_core help file:

    $ pip install hcli_core

    $ hcli_core help

    $ gunicorn --workers=5 --threads=2 --chdir \`hcli_core path\` "hcli_core:HCLI().connector"

If you want to load a sample HCLI other than the default, you can try loading the sample hfm. A folder path to any 3rd party HCLI module can be provided in the same way:

    $ gunicorn --workers=5 --threads=2 --chdir \`hcli_core path\` "hcli_core:HCLI(\\"\`hcli_core sample hfm\`\\").connector"

Curl your new service to understand what is being exposed. The HCLI root URL, to use with an HCLI client, is the cli link relation:

    $ curl http://127.0.0.1:8000

Install an HCLI client, for example Huckle (https://github.com/cometaj2/huckle), and access the default sample jsonf CLI
exposed by HCLI Core (you may need to restart your terminal to be able to use jsonf by name directly):

    $ pip install huckle

    $ huckle cli install http://127.0.0.1:8000

    $ jsonf help

You can also look at the huckle help file:

    $ huckle help

Bugs
----

- No good handling of control over request and response in cli code which can lead to exceptions and empty response client side.

.. |build status| image:: https://travis-ci.org/cometaj2/hcli_core.svg?branch=master
.. _build status: https://travis-ci.org/cometaj2/hcli_core
.. |pypi| image:: https://badge.fury.io/py/hcli-core.svg
.. _pypi: https://badge.fury.io/py/hcli-core
