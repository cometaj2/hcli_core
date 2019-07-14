import json
import data
from ipaddress import *

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
    
    def listFreeSubnets(self):
        subnets = ""
        for index, value in enumerate(self.free):
            subnets = subnets + value + "\n"

        return subnets

    def listFreeSubnetsWithPrefix(self, prefix):
        subnets = ""
        for index, value in enumerate(self.free):
            ip = ip_network(self.free[index])

            try:
                s = list(ip.subnets(new_prefix=int(prefix.replace("'", "").replace("\"", ""))))
                for i in s:
                    subnets = subnets + str(i) + "\n"
            except:
                pass

        return subnets

    def allocateSubnet(self, prefix):
        subnet = ""
        for index, value in enumerate(self.free):
            ip = ip_network(self.free[index])

            try:
                s = list(ip.subnets(new_prefix=int(prefix.replace("'", "").replace("\"", ""))))
                if len(s) != 0:
                    subnet = subnet + str(s[0]) + "\n"
                    if str(s[0]) not in self.allocated:
                        self.allocated.append(str(s[0]))
                    self.free.remove(value)
                    s = s[1:len(s)]
                    t = collapse_addresses(s)
                    for i in t:
                        try:
                            if i not in self.free:
                                self.free.append(str(i))
                        except:
                            pass

                    
                    data.DAO(self).save()
                    return subnet
                else:
                    return subnet
            except:
                pass

        return subnet
