import json
from collections import namedtuple

class DAO:
    """ Adds an object's attributes verbatim to a resource """
    def __init__(self, model):
        for key, value in vars(model).items():
            setattr(self, key, value)

    """ Serializes an inherently well structured haliot resource to application/hal+json """
    def serialize(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
                          sort_keys=True,
                          indent=4)

    def deserialize(self, obj=None):
        x = json.loads(obj, self=lambda d: namedtuple('X', d.keys())(*d.values()))
        print(x)
