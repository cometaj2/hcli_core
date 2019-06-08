import json

class Resource:
    _links = None

    """ Adds a object's attributes verbatim to a haliot resource """
    def __init__(self, model):
        self._links = {}
        for key, value in vars(model).items():
            setattr(self, key, value)

    """ Adds a link to the current haliot resource while maintaining its inherently well structured hal+json like form """
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


    """ Serializes an inherently well structured haliot resource to application/hal+json """
    def serialize(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
                          sort_keys=True,
                          indent=4)

class Link:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
