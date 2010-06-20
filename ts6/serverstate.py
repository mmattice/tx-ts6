import time
from ts6.channel import Channel

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

    def Client(self, uid):
        return self.cbyuid[uid]

    def addClient(self, client):
        self.cbyuid[client.uid] = client
        self.cbynick[client.nick.lower()] = client

    def delClient(self, client = None, uid = None):
        if client:
            uid = client.uid
        del(self.cbynick[client.nick.lower()])
        del(self.cbyuid[uid])

    def NickChange(self, uid, newnick, ts):
        c = self.Client(uid)
        oldnick = c.nick
        self.cbynick[newnick.lower()] = self.cbynick.pop(oldnick.lower())
        c.nick = newnick
        c.ts = ts
        c.identified = False

    def Join(self, client, channelname):
        cn = channelname.lower()
        tc = self.chans.get(cn, None)
        if not tc:
            tc = Channel(cn, 'nt', int(time.time()))
            self.chans[cn] = tc
        if client not in tc.clients:
            self.conn.sjoin(client, tc)
            tc.joined(client)

    def Part(self, client, channelname, reason=None):
        cn = channelname.lower()
        tc = self.chans[cn]
        if client in tc.clients:
            self.conn.part(client, tc, reason)
            tc.left(client, reason)

    def Away(self, uid, msg):
        c = self.Client(uid)
        c.away = msg

    def addServer(self, server):
        self.sbysid[server.sid] = server
        self.sbyname[server.name] = server
