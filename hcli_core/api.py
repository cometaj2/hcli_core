import falcon
import json
import halogen
import semantics
import template
import home

class HomeApi():
    def __init__(self):
        self.controller = home.HomeController()

    def on_get(self, req, resp) -> None:
        t = template.Template()

        serialized = home.HomeController.serialize(home.Home())
        resp.body = json.dumps(serialized)
