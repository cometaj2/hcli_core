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
    
    def listFreeNetworks(self):
        subnets = ""
        for pindex, pool in enumerate(self.pools):
            if len(pool["free"]) > 0:
                subnets = subnets + "------------------------------" + "\n"
            for index, value in enumerate(pool["free"]):
                subnets = subnets + pool["name"] + " (free)      " + value + "\n"

        return subnets

    def listAllocatedNetworks(self):
        subnets = ""
        for pindex, pool in enumerate(self.pools):
            if len(pool["allocated"]) > 0:
                subnets = subnets + "------------------------------" + "\n"
            for index, value in enumerate(pool["allocated"]):
                subnets = subnets + pool["name"] + " (allocated)      " + value + "\n"

        return subnets

    def listFreeNetworksWithPrefix(self, prefix):
        subnets = ""
        for pindex, pool in enumerate(self.pools):
            for index, value in enumerate(pool["free"]):
                ip = ip_network(pool["free"][index])

                try:
                    s = list(ip.subnets(new_prefix=int(prefix.replace("'", "").replace("\"", ""))))
                    if len(s) > 0:
                        subnets = subnets + "------------------------------" + "\n"
                    for i in s:
                        subnets = subnets + pool["name"] + " (free)      " + str(i) + "\n"
                except:
                    pass

        return subnets

    def createLogicalGroup(self, groupname):
        cleanname = groupname.replace("'", "").replace("\"", "")
        self.pools.append(pool.Pool(cleanname))
        data.DAO(self).save()
        return cleanname + "\n"

    def allocateNetwork(self, groupname, prefix):
        subnet = ""
        for pindex, pool in enumerate(self.pools):
            if pool["name"] == groupname.replace("'", "").replace("\"", ""):
                pool["free"].sort(key=lambda network: int(network.split("/")[1]), reverse=True)
                for index, value in enumerate(pool["free"]):
                    ip = ip_network(pool["free"][index])

                    try:
                        s = list(ip.subnets(new_prefix=int(prefix.replace("'", "").replace("\"", ""))))
                        if len(s) != 0:
                            subnet = subnet + str(s[0]) + "\n"
                            if str(s[0]) not in pool["allocated"]:
                                pool["allocated"].append(str(s[0]))
                            pool["free"].remove(value)
                            s = s[1:len(s)]
                            t = collapse_addresses(s)
                            for i in t:
                                try:
                                    if i not in pool["free"]:
                                        pool["free"].append(str(i))
                                except:
                                    pass
    
                            pool["free"].sort(key=lambda network: int(network.split("/")[1]), reverse=True)
                            data.DAO(self).save()
                            return subnet
                        else:
                            return subnet
                    except:
                        pass

        return subnet
