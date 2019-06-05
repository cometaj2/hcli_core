import json

class Resource:
    _links = None

    def __init__(self, model):
        self._links = {}
        for key, value in vars(model).items():
            setattr(self, key, value)

    def addLink(self, rel, link):
        if link != None:
            if rel == "self":
                self._links[rel]=link
            if rel != "self":
                l = self._links.get(rel)
                if l:
                    self._links[rel].append(link)
                else:
                    self._links[rel]=[]
                    self._links[rel].append(link)

    def toHALJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
                          sort_keys=True,
                          indent=4)

class Link:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
