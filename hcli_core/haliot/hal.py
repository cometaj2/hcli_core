import json

class Resource:
    _links = None

    def __init__(self, model):
        self._links = {}
        for key, value in vars(model).items():
            setattr(self, key, value)

    def addLink(self, link):
        if link != None:
            for key, value in vars(link).items():
                l = dict(key=key)
                self._links.update(self=value)

    def toHALJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
                          sort_keys=True,
                          indent=4)

class Link:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
