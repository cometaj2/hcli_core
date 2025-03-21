|pypi| |build status| |pyver| |huckle| |hc| |hg|

HCLI Core
=========

An HCLI Connector that can be used to expose a REST API that behaves as a CLI, via hypertext
command line interface (HCLI) semantics.

----

HCLI Core implements an HCLI Connector, a type of Service Connector, as a WSGI application, and provides a way
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

Related HCLI Projects
---------------------

- hcli-hc, a python package for an HCLI (hc) that can act both as a gcode streamer (e.g. for OpenBuilds Blackbox controller v1.1g) and CNC interface. In other words, this HCLI acts in the same capacity as the OpenBuilds CONTROL software and OpenBuilds Interface CNC Touch hardware to help control a GRBL v1.1g controlled CNC. [5]

- hcli-hai, a python package wrapper for an HCLI (hai) that can interact with LLMs via terminal input and output streams. [6]

[5] https://github.com/cometaj2/hcli_hc

[6] https://github.com/cometaj2/hcli_hai

Installation
------------

hcli_core requires a supported version of Python and pip.

You'll need an WSGI compliant application server to run hcli_core. For example, you can use Green Unicorn (https://gunicorn.org/), and an
HCLI client such as Huckle (https://github.com/cometaj2/huckle). The following runs the default *jsonf* HCLI bundled with HCLI Core.


.. code-block:: console

    pip install hcli-core
    pip install gunicorn
    pip install huckle
    gunicorn --workers=1 --threads=2 -b 127.0.0.1:8000 "hcli_core:connector()"

Usage
-----

Open a different shell window.

Setup the huckle env eval in your .bash_profile (or other bash configuration) to avoid having to execute eval everytime you want to invoke HCLIs by name (e.g. jsonf).

Note that no CLI is actually installed by Huckle. Huckle reads the HCLI semantics exposed by the API and ends up behaving *like* the CLI it targets.


.. code-block:: console

    huckle cli install http://127.0.0.1:8000
    eval $(huckle env)
    jsonf help

3rd Party HCLI Installation
---------------------------

If you want to load a sample HCLI other than the default sample application, you can try loading one of the other sample HCLIs
developped independently of HCLI Core. For example, the *hai* HCLI (hypertext LLM command line chat application).

A folder path to any other 3rd party HCLI can be provided in the same way to the HCLI Connector, provided the 3rd party HCLI meets
CLI interface (cli.py) and HCLI template (template.json) requirements:

.. code-block:: console

    pip install hcli-hai
    pip install hcli-core
    pip install gunicorn
    pip install huckle
    gunicorn --workers=1 --threads=2 "hcli_core:connector(\"`hcli_hai path`\")"

3rd Party HCLI Usage
--------------------

Open a different shell window.

Setup the huckle env eval in your .bash_profile (or other bash configuration) to avoid having to execute eval everytime you want to invoke HCLIs by name (e.g. hai).

.. code-block:: console
    
    huckle cli install http://127.0.0.1:8000
    eval $(huckle env)
    hai help

Versioning
----------
    
This project makes use of semantic versioning (http://semver.org) and may make use of the "devx",
"prealphax", "alphax" "betax", and "rcx" extensions where x is a number (e.g. 0.3.0-prealpha1)
on github. Only full major.minor.patch releases will be pushed to pip from now on.

Supports
--------

- HTTP/HTTPS.
- HCLI version 1.0 server semantics for hal+json.
- Web Server Gateway Interface (WSGI) through PEP 3333 and Falcon.
- Bundled Sample HCLIs:
    - jsonf - a simple formatter for JSON.
    - hfm   - a file upload and download manager that works with \*nix terminal shell input and output streams.
    - hptt  - a rudimentary HCLI Push To Talk (PTT) channel management service.
    - hub   - a rudimentary HCLI service discovery hub.
    - nw    - a flexible IP Address Management (IPAM) service.
- Support for use of any 3rd party HCLI code that meets CLI interface requirements and HCLI template requirements (i.e. see sample HCLIs).
- Support large input and output streams as application/octet-stream.
- HTTP Basic Authentication.  See hcli_core help for details.
- HCLI Core API Key (HCOAK) Authencitation. See hcli_core help for details.
- Support HTTP API Problem Details [RFC9457] per spec to help with client-side STDERR output.
- Credentials Management via the hco HCLI.
- Centralized remote authentication support via hco for HCLI Core services configured for remote credential management.
- Serverless deployment (i.e. AWS Lambda).

Authentication
--------------

HCLI Core makes available the deployment of an HCLI Management app (hco) to manage authentication credentials for the deployed 3rd party HCLI service, and can be configured for authentication in two distinct ways:

- local - HCLI Core manages the credentials locally for the 3rd party HCLI app.
- remote - HCLI Core forwards credentials validation to a remotely hosted hco for 3rd party HCLI app access.

The remote configuration allows for centralized remote authentication support across many deployed HCLIs. This is trivially accomplished via HCLI Core making use of the huckle HCLI client, and via hco and HCLI semantics, to forward validation of provided credentials to a remotely hosted hcli_core service exposing hco. See 'hcli_core help' for details.

Artificial Intelligence
-----------------------

HCLI naturally presents, via in-band documentation availability, as a highly discoverable semantic landscape that can be used to trivially extend the capabilities of conversational LLMs by providing a mature conceptual and practical alternative to Model Context Protocol (MCP) or function calls.

This is explored via hcli_hai https://github.com/cometaj2/hcli_hai and haillo https://github.com/cometaj2/haillo

Security
--------

HCLI Core implements a trusted integration model. In other words, 3rd party HCLIs running via HCLI Core MUST be trusted not to interfere with HCLI Core. 3rd party HCLIs are inherently able to do anything that Python can do, and as such, a 3rd party HCLI cannot coherently be isolated from HCLI Core as a security boundary. If a trust boundary needs to be established on authentication grounds, then authentication SHOULD be managed elsewhere (i.e. by another layer on the network or via a remotely hosted hco; see Authentication).

To Do
-----

- Automated tests for all bundled HCLI samples.
- Separate out HCLI applications from HCLI Core to help avoid application dependencies bleeding onto HCLI Core.
- Rate limiting.
- Lockout on multiple failed authentications.
- Better role handling for admin vs users for remote validation.
- Better logging configuration support.
- Role assignment for hco remote validation authorization.

Bugs
----

- No good handling of control over request and response in cli code which can lead to exceptions and empty response client side.
- The hfm sample HCLI fails disgracefully when copying a remote file name that doesn't exist (server error).
- Routing can ambiguous and fail if the 3rd party HCLI app's name start with hco in core.root aggregate configuration (template.py owns)

.. |build status| image:: https://circleci.com/gh/cometaj2/hcli_core.svg?style=shield
   :target: https://circleci.com/gh/cometaj2/hcli_core
.. |pypi| image:: https://img.shields.io/pypi/v/hcli-core?label=hcli-core
   :target: https://pypi.org/project/hcli-core
.. |pyver| image:: https://img.shields.io/pypi/pyversions/hcli-core.svg
   :target: https://pypi.org/project/hcli-core
.. |huckle| image:: https://img.shields.io/pypi/v/huckle?label=huckle
   :target: https://pypi.org/project/huckle
.. |hc| image:: https://img.shields.io/pypi/v/hcli-hc?label=hcli-hc
   :target: https://pypi.org/project/hcli-hc
.. |hg| image:: https://img.shields.io/pypi/v/hcli-hg?label=hcli-hai
   :target: https://pypi.org/project/hcli-hai
