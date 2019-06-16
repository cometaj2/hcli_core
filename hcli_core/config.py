from __future__ import absolute_import, division, print_function

import os

root = os.path.abspath(os.path.dirname(__file__))
hcli_core_manpage_path = root + "/data/hcli_core.1"
template = None

""" We parse the HCLI json template to load the HCLI navigation in memory """
def parse_template(t):
    global template
    template = t
