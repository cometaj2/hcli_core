import json
import data

class Pool:
    name = None
    allocated = None
    free = None
    
    def __init__(self, groupname, networks=None):
        self.name = groupname
        self.allocated = []
        if networks != None:
            self.free = ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]
        else:
            self.free = []

    def serialize(self):
        return data.DAO(self).serialize()   
