import json
import data

class Networks:
    allocated = None
    free = None

    def __init__(self):
        if not data.DAO().exists():
            self.allocated = []
            self.free = ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]
            data.DAO(self).save()

        else:
            data.DAO().load(self)

    def serialize(self):
        return data.DAO(self).serialize()   
    
    def listFreeRanges(self):
        ranges = ""
        for index, i in enumerate(self.free):
            ranges = ranges + index + "\n"

        return ranges
