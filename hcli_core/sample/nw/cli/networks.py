import json
import data
import pool
from ipaddress import *

class Networks:
    pools = None

    def __init__(self):
        if not data.DAO().exists():
            self.pools = []
            self.pools.append(pool.Pool("default", ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]))
            data.DAO(self).save()
            data.DAO().load(self)

        else:
            data.DAO().load(self)

    def serialize(self):
        return data.DAO(self).serialize()   

    # lists allocatable networks across all logical groups.
    def listFreeNetworks(self):
        subnets = ""
        for pindex, pool in enumerate(self.pools):
            if len(pool["free"]) > 0:
                subnets = subnets + "------------------------------" + "\n"
            for index, value in enumerate(pool["free"]):
                subnets = subnets + pool["name"] + " (free)      " + value + "\n"

        return subnets

    # lists all allocated networks for all logical groups
    def listAllocatedNetworks(self):
        subnets = ""
        for pindex, pool in enumerate(self.pools):
            if len(pool["allocated"]) > 0:
                subnets = subnets + "------------------------------" + "\n"
            for index, value in enumerate(pool["allocated"]):
                subnets = subnets + pool["name"] + " (allocated)      " + value + "\n"

        return subnets

    # lists free/available networks, across all logical groups, that match the provided prefix
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

    # create a new logical group (pool) to allocate networks from
    def createLogicalGroup(self, groupname):
        cleanname = groupname.replace("'", "").replace("\"", "")
        for pindex, p in enumerate(self.pools):
            if p["name"] == cleanname:
                return ""

        self.pools.append(pool.Pool(cleanname))
        data.DAO(self).save()
        return cleanname + "\n"

    # rename a logical group
    def renameLogicalGroup(self, oldname, newname):
        cleanold = oldname.replace("'", "").replace("\"", "")
        cleannew = newname.replace("'", "").replace("\"", "")

        for pindex, p in enumerate(self.pools):
            if p["name"] == cleannew:
                return ""

        for pindex, p in enumerate(self.pools):
            if p["name"] == cleanold:
                p["name"] = cleannew
                data.DAO(self).save()
                return cleannew + "\n"

        return ""

    # remove a named group from the available pools
    def removeLogicalGroup(self, groupname):
        cleanname = groupname.replace("'", "").replace("\"", "")
        for pindex, pool in enumerate(self.pools):
            if pool["name"] == cleanname:
                del self.pools[pindex]
                data.DAO(self).save()
                return cleanname + "\n"

        return ""

    # list named group from the available pools
    def listLogicalGroup(self):
        groups = ""
        for pindex, pool in enumerate(self.pools):
            groups = groups + pool["name"] + "\n"

        return groups

    # Allocate the next available network that matches the provided previx. gives precedence to smaller networks.
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
                            if str(s[0]) not in pool["allocated"]:
                                pool["allocated"].append(str(s[0]))
                            pool["free"].remove(value)
                            ipnetwork = s[0]
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
                            subnet = subnet + str(ipnetwork) + "\n"
                            return subnet
                        else:
                            return subnet
                    except:
                        pass

        return subnet

    # allocate a specific provided network for a given logical group if the provided network is allocatable (free)
    def allocateSpecificNetwork(self, groupname, network):
        subnet = ""
        network = network.replace("'", "").replace("\"", "")
        ipnetwork = ip_network(network)
        prefix = network.split("/")[1]
        for pindex, pool in enumerate(self.pools):
            if pool["name"] == groupname.replace("'", "").replace("\"", ""):
                for index, value in enumerate(pool["free"]):
                    ip = ip_network(pool["free"][index])
                    try:
                        s = list(ip.subnets(new_prefix=int(prefix)))
                        if len(s) != 0:
                            if ipnetwork in s:
                                if str(ipnetwork) not in pool["allocated"]:
                                    pool["allocated"].append(str(ipnetwork))
                                else:
                                    return subnet
                                pool["free"].remove(value)
                                s.remove(ipnetwork)
                                t = collapse_addresses(s)
                                for i in t:
                                    try:
                                        if i not in pool["free"]:
                                            pool["free"].append(str(i))
                                    except:
                                        pass

                                pool["free"].sort(key=lambda network: int(network.split("/")[1]), reverse=True)
                                data.DAO(self).save()
                                subnet = subnet + str(ipnetwork) + "\n"
                                return subnet

                        else:
                            return subnet
                    except:
                        pass

        return subnet

    # deallocate a specific CIDR range from a logical group if the provided network matches exactly
    def deallocateSpecificNetwork(self, groupname, network):
        self.compactFreeNetworks(groupname)
        subnet = ""
        network = network.replace("'", "").replace("\"", "")
        prefix = network.split("/")[1]
        for pindex, pool in enumerate(self.pools):
            if pool["name"] == groupname.replace("'", "").replace("\"", ""):
                for index, value in enumerate(pool["allocated"]):
                    ip = pool["allocated"][index]
                    try:
                        if network == ip:
                            pool["allocated"].remove(network)
                            pool["free"].append(network)
                            self.compactFreeNetworks(groupname) 
                            data.DAO(self).save()
                            subnet = subnet + network + "\n"
                            return subnet

                    except:
                        pass

        return subnet

    # add an additional free CIDR block to the pool if it doesn't overlap with existing free or allocated CIDRs
    def addSpecificFreeNetwork(self, groupname, network):
        network = network.replace("'", "").replace("\"", "")
        ipnetwork = ip_network(network)
        prefix = network.split("/")[1]
        for pindex, pool in enumerate(self.pools):
            if pool["name"] == groupname.replace("'", "").replace("\"", ""):
                for index, value in enumerate(pool["free"]):
                    ipnetworks = ip_network(pool["free"][index])
                    if ipnetwork.overlaps(ipnetworks):
                        return ""
                for jindex, jvalue in enumerate(pool["allocated"]):
                    jipnetworks = ip_network(pool["allocated"][jindex])
                    if ipnetwork.overlaps(jipnetworks):
                        return ""

                pool["free"].append(network)
                self.compactFreeNetworks(groupname)
                data.DAO(self).save()
                return network + "\n"

        return ""

    def removeSpecificFreeNetwork(self, groupname, network):
        subnet = ""
        network = network.replace("'", "").replace("\"", "")
        ipnetwork = ip_network(network)
        prefix = network.split("/")[1]
        for pindex, pool in enumerate(self.pools):
            if pool["name"] == groupname.replace("'", "").replace("\"", ""):
                for index, value in enumerate(pool["free"]):
                    ip = ip_network(pool["free"][index])
                    try:
                        s = list(ip.subnets(new_prefix=int(prefix)))
                        if len(s) != 0:
                            if ipnetwork in s:
                                pool["free"].remove(value)
                                s.remove(ipnetwork)
                                t = collapse_addresses(s)
                                for i in t:
                                    try:
                                        if i not in pool["free"]:
                                            pool["free"].append(str(i))
                                    except:
                                        pass

                                pool["free"].sort(key=lambda network: int(network.split("/")[1]), reverse=True)
                                data.DAO(self).save()
                                subnet = subnet + str(ipnetwork) + "\n"
                                return subnet

                        else:
                            return subnet
                    except:
                        pass

        return subnet

    def compactFreeNetworks(self, groupname):
        new = []
        for pindex, pool in enumerate(self.pools):
            if pool["name"] == groupname.replace("'", "").replace("\"", ""):
                for index, value in enumerate(pool["free"]):
                    network = ip_network(pool["free"][index])
                    new.append(network)
                collapsed = collapse_addresses(new)
                pool["free"] = [str(network) for network in collapsed]
                pool["free"].sort(key=lambda network: int(network.split("/")[1]), reverse=True)
                return
