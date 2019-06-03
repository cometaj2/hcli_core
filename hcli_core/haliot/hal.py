import json

class Resource:
    _links = None

    def __init__(self, model):
        self._links = []
        for attr, value in vars(model).items():
            setattr(self, attr, value)

    def Link(self, link):
        if link != None:
            #for key, value in enumerate(link):
            #    setattr(self._links, key, value)
            self._links.append(link)
            #setattr(self._links, key="self" ,link)

    def toHALJSON(self):
        #for index, i in enumerate(self._links):
        #    self._links[index]
        #    print(self._links[index])
        
        return json.dumps(self, default=lambda o: o.__dict__, 
                          sort_keys=True,
                          indent=4)

class Link:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
