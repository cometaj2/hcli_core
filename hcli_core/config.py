from __future__ import absolute_import, division, print_function

# These next 2 variables are dynamically updated from read request
host = None
port = None

# parses the configuration of a given cli to set configured execution
def authority(hostvalue, portvalue):
    global host
    host = hostvalue
    global port
    port = portvalue
