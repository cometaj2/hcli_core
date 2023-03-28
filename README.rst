HCLI Core |pyver|_ |build status|_ |pypi|_
==========================================

An HCLI Connector that can be used to expose a REST API with a built-in CLI, via hypertext
command line interface (HCLI) semantics.

----

HCLI Core implements an HCLI Connector, a type of Service Connector, as a WSGI application and provides a way
for developers to expose a service hosted CLI, as a REST API, via HCLI semantics. Such an API exposes a "built-in"
CLI that can be interacted with dynamically with any HCLI client. Up to date, in-band, man page style API/CLI
documentation is readily available for use to help understand how to interact with the API.

Most, if not all, programming languages have a way to issue shell commands. With the help
of a generic HCLI client, such as Huckle [1], APIs that make use of HCLI semantics are readily consumable
anywhere via the familiar command line (CLI) mode of operation, and this, without there being a need to write
a custom and dedicated CLI to interact with a specific HCLI API.

You can find out more about HCLI on hcli.io [2]

The HCLI Internet-Draft [3] is a work in progress by the author and 
the current implementation leverages hal+json alongside a static form of ALPS
(semantic profile) [4] to help enable widespread cross media-type support.

Help shape HCLI and it's ecosystem by raising issues on github!

[1] https://github.com/cometaj2/huckle

[2] http://hcli.io

[3] https://github.com/cometaj2/I-D/tree/master/hcli

[4] http://alps.io

Installation
------------

hcli_core requires a supported version of Python and pip.

You'll need an WSGI compliant application server to run hcli_core. For example, you can use Green Unicorn (https://gunicorn.org/)

.. code-block:: console

    pip install gunicorn

Install hcli_core via pip. You can launch gunicorn from anywhere by using "hcli_core path". You can also look at the hcli_core help file.

You can curl your new service to understand what is being exposed. The HCLI root URL, to use with an HCLI client, is the cli link relation.

Install an HCLI client, for example Huckle (https://github.com/cometaj2/huckle), and access the sample CLI (e.g. jsonf or hg)
exposed by HCLI Core. You may need to restart your terminal to be able to use the sample CLI by name directly (e.g. jsonf or hg); otherwise you can attempt
to source ~/.bash_profile or ~/.bashrc).

Note that no CLI is actually installed by huckle. Huckle reads the HCLI semantics dynamically and ends up behaving *like* the CLI it targets:

.. code-block:: console

    pip install hcli_core

    hcli_core help

    gunicorn --workers=5 --threads=2 -b 127.0.0.1:8000 --chdir `hcli_core path` "hcli_core:connector()"
    
    curl http://127.0.0.1:8000
    
    pip install huckle
    
    huckle help

    huckle cli install http://127.0.0.1:8000

    jsonf help

If you want to load a sample HCLI other than the default sample application, you can try loading the sample *hg* HCLI (hypertext GPT-3.5 chatbot).
A folder path to any other 3rd party HCLI can be provided in the same way:

.. code-block:: console

    gunicorn --workers=5 --threads=2 --chdir `hcli_core path` "hcli_core:connector(\"`hcli_core sample hg`\")"

    huckle cli install http://127.0.0.1:8000

    hg help

Bugs
----

- No good handling of control over request and response in cli code which can lead to exceptions and empty response client side.
- The hfm sample HCLI fails disgracefully when copying a remote file name that doesn't exist (server error).

.. |build status| image:: https://circleci.com/gh/cometaj2/hcli_core.svg?style=shield
.. _build status: https://circleci.com/gh/cometaj2/huckle
.. |pypi| image:: https://badge.fury.io/py/hcli-core.svg
.. _pypi: https://badge.fury.io/py/hcli-core
.. |pyver| image:: https://img.shields.io/pypi/pyversions/hcli-core.svg
.. _pyver: https://pypi.python.org/pypi/hcli-core
