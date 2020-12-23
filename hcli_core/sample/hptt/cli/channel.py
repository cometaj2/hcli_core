import json
import data
import hashlib
import base64

class Channel:
    name = None
    owner = None
    members = None
    stream = None

    def __init__(self, name, owner=None, members=None):
        self.name = name
        self.owner = owner
        self.stream = {}
        uniqueinstreamid = self.owner + self.name + "instream"
        uniqueoutstreamid = self.owner + self.name + "outstream"

        self.stream['in'] = "/" + hashlib.sha256(uniqueinstreamid.encode('utf-8')).hexdigest()
        self.stream['out'] = "/" + hashlib.sha256(uniqueoutstreamid.encode('utf-8')).hexdigest()
        
        if members != None:
            self.members = members
        else:
            self.members = []

    def serialize(self):
        return data.DAO(self).serialize()   
