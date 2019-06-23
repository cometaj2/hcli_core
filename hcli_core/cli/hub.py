import data
import namespace as ns

class Hub:
    namespace = None

    def __init__(self, hub=None):
        self.namespace = []
        self.namespace.append(ns.Namespace())

    def serialize(self):
        return data.DAO(self).serialize()   
    
    def listNamespace(self):
        for index, i in enumerate(self.namespace):
            arg = self.namespace[index]
            print( arg  )
