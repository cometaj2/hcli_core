import json
import data
import hashlib
import base64

class Channel:
    name = None
    owners = None
    members = None

    def __init__(self, name, owners=None, members=None):
        self.name = name

        if owners != None:
            self.owners = owners
        else:
            self.owners = []

        if members != None:
            self.members = members
        else:
            self.members = []

    def serialize(self):
        return data.DAO(self).serialize()   
