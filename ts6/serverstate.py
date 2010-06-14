class ServerState:
    def __init__(self):
        self.sid = '99Z'
        self.servername = 'ts6.local'
        self.serverdesc = 'twisted-ts6 test'
        self.chans = {}
        self.sbysid = {}
        self.sbyname = {}
        self.cbyuid = {}
        self.cbynick = {}
        self.nextuid = [ 0, 0, 0, 0, 0, 0 ]
        self.uidchars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'

    def mkuid(self):
        uid = self.nextuid
        for i in range(5, 0, -1):
            if self.nextuid[i] != (ord('z') - ord('a') + 10):
                self.nextuid[i] += 1
                break
            self.nextuid[i] = 0
        return ''.join([self.uidchars[x] for x in uid])

    def cleanNonLocal(self):
        """ remove all clients and servers from local state """
        for uid in self.cbyuid.keys():
            if uid[:3] == self.sid:
                continue
            c = self.cbyuid[uid]
            for h in c.chans:
                h.parted(c, 'netsplit')
                if len(h.clients) == 0:
                    del(self.chans[h.name.lower()])
            del(self.cbynick[c.nick.lower()])
            del(self.cbyuid[uid])
        for sid in self.sbysid.keys():
            if sid == self.sid:
                continue
            s = self.sbysid[sid]
            del(self.sbyname[s.name])
            del(self.sbysid[sid])

