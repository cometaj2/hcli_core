import json
import data
import channel

class Channels:
    channels = None

    def __init__(self):
        if not data.DAO().exists():
            self.channels = []
            self.channels.append(channel.Channel("default", ['http://hcli.io'], ['http://hcli.io']))
            data.DAO(self).save()
            data.DAO().load(self)

        else:
            data.DAO().load(self)

    def serialize(self):
        return data.DAO(self).serialize()   

    # create a new channel to chat or associate to half-duplex PTT networks.
    def createLogicalChannel(self, channelname):
        cleanname = channelname.replace("'", "").replace("\"", "")
        for pindex, p in enumerate(self.channels):
            if p["name"] == cleanname:
                return ""

        self.channels.append(channel.Channel(cleanname))
        data.DAO(self).save()
        return cleanname + "\n"

    # rename a channel
    def renameLogicalChannel(self, oldname, newname):
        cleanold = oldname.replace("'", "").replace("\"", "")
        cleannew = newname.replace("'", "").replace("\"", "")

        for pindex, p in enumerate(self.channels):
            if p["name"] == cleannew:
                return ""

        for pindex, p in enumerate(self.channels):
            if p["name"] == cleanold:
                p["name"] = cleannew
                data.DAO(self).save()
                return cleannew + "\n"

        return ""

    # remove a named channel from the available channels
    def removeLogicalChannel(self, channelname):
        cleanname = channelname.replace("'", "").replace("\"", "")
        for pindex, channel in enumerate(self.channels):
            if channel["name"] == cleanname:
                del self.channels[pindex]
                data.DAO(self).save()
                return cleanname + "\n"

        return ""

    # list named channels from the available channels
    def listLogicalChannel(self):
        channels = ""
        for pindex, channel in enumerate(self.channels):
            channels = channels + channel["name"] + "\n"

        return channels

    # acquire channel push to talk (ptt) by channel name
    def acquire(self, channelname):
        for pindex, c in enumerate(self.channels):
            if c["name"] == channelname:
                c["ptt"] = "active"
                data.DAO(self).save()
                return True

        return False

    # release channel push to talk (ptt) by channel name
    def release(self, channelname):
        for pindex, c in enumerate(self.channels):
            if c["name"] == channelname:
                c["ptt"] = "inactive"
                data.DAO(self).save()
                return True

        return False

    # get channel ptt status
    def getPttStatus(self, channelname):
        for pindex, c in enumerate(self.channels):
            if c["name"] == channelname:
                return c["ptt"] + "\n"

        return ""
