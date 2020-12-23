import os
import inspect
import re

class Chroot:
    root = os.path.dirname(inspect.getfile(lambda: None))
    chroot = root + "/chroot"
    pwd = chroot
    
    def __init__(self):
        if not os.path.exists(self.chroot):
            os.makedirs(self.chroot)

    """ translates a provided path into an absolute chrooted path to lock down access to the chroot folder """
    def translate(self, path):
        newpath = path.strip()
        newpath = re.sub(r'\.+/', "/", newpath)
        newpath = re.sub(r'/+', "/", newpath)
        newpath = newpath.rstrip("/")
        if newpath[:1] == "/":
            lockpath = self.chroot + "/" + newpath[1:]
            return lockpath

        return self.pwd + "/" + newpath
