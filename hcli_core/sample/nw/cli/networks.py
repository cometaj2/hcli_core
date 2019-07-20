import json
import data
import pool
from ipaddress import *

class Networks:
    pools = None
    
    def __init__(self):
        if not data.DAO().exists():
            self.pools = []
            self.pools.append(pool.Pool("default"))
            data.DAO(self).save()

        else:
            data.DAO().load(self)

    def serialize(self):
        return data.DAO(self).serialize()   
    
    def listFreeSubnets(self):
        subnets = ""
        for pindex, pool in enumerate(self.pools):
            subnets = subnets + "------------------------------" + "\n"
            subnets = subnets + pool["name"] + "\n"
            for index, value in enumerate(pool["free"]):
                subnets = subnets + value + "\n"

        return subnets

    def listFreeSubnetsWithPrefix(self, prefix):
        subnets = ""
        for pindex, pool in enumerate(self.pools):
            subnets = subnets + "------------------------------" + "\n"
            subnets = subnets + pool["name"] + "\n"
            for index, value in enumerate(pool["free"]):
                ip = ip_network(pool["free"][index])

                try:
                    s = list(ip.subnets(new_prefix=int(prefix.replace("'", "").replace("\"", ""))))
                    for i in s:
                        subnets = subnets + str(i) + "\n"
                except:
                    pass

        return subnets

    def createLogicalGroup(self, groupname):
        group = ""
        for index, value in enumerate(self.free):
            ip = ip_network(self.free[index])

            try:
                s = list(ip.subnets(new_prefix=int(prefix.replace("'", "").replace("\"", ""))))
                for i in s:
                    subnets = subnets + str(i) + "\n"
            except:
                pass

        data.DAO(self).save()
        return subnets

    def allocateSubnet(self, prefix):
        subnet = ""
        self.free.sort(key=lambda network: int(network.split("/")[1]), reverse=True)
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

                    self.free.sort(key=lambda network: int(network.split("/")[1]), reverse=True)
                    data.DAO(self).save()
                    return subnet
                else:
                    return subnet
            except:
                pass

        return subnet
