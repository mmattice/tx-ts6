import time
from ts6.channel import Channel

class ServerState:
    def __init__(self):
        self.conn = None
        self.sid = '99Z'
        self.servername = 'ts6.local'
        self.serverdesc = 'twisted-ts6 test'
        self.chans = {}
        self.chansbyuid = {}
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
                h._left(c, 'netsplit')
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

    def burst(self):
        """ Handle pushing all known state to opposite end of connection """
        for uid, c in self.cbyuid.iteritems():
            if c.conn:
                self.conn.introduce(c)
        for channame, channel in self.chans.iteritems():
            self.conn.burstchan(channel)

    def Channel(self, chref):
        if str(type(chref)) == """<type 'str'>""":
            chref = self.chans[chref.lower()]
        return chref

    def ClientByNick(self, nick):
        return self.cbynick[nick.lower()]

    def Client(self, uid):
        return self.cbyuid[uid]

    def addClient(self, client):
        self.cbyuid[client.uid] = client
        self.chansbyuid[client.uid] = set()
        self.cbynick[client.nick.lower()] = client
        if client.conn:
            self.conn.introduce(client)

    def delClient(self, client = None, uid = None):
        if client:
            uid = client.uid
        del(self.cbynick[client.nick.lower()])
        del(self.chansbyuid[uid])
        del(self.cbyuid[uid])

    def NickChange(self, uid, newnick, ts):
        c = self.Client(uid)
        oldnick = c.nick
        self.cbynick[newnick.lower()] = self.cbynick.pop(oldnick.lower())
        c.nick = newnick
        c.ts = ts
        c.identified = False
        for nick, lc in self.cbynick.iteritems():
            if (lc.conn and (lc != c)):
                lc._userRenamed(oldnick, c)

    def Join(self, client, channel):
        created = False
        if getattr(channel, 'name', None):
            tc = channel
        else:
            cn = channel.lower()
            tc = self.chans.get(cn, None)
        if not tc:
            tc = Channel(cn, 'nt', int(time.time()))
            self.chans[cn] = tc
            created = True
        if client not in tc.clients:
            if self.conn:
                if created:
                    self.conn.sjoin(client, tc)
                else:
                    self.conn.join(client, tc)
            self.chansbyuid[client.uid].add(tc)
            tc.joined(client)

    def Part(self, client, channel, reason=None):
        """ called from Conn.got_part and ServerState.leave """
        tc = self.Channel(channel)
        self.chansbyuid[client.uid].remove(tc)
        if client in tc.clients:
            if client.conn:
                self.conn.part(client, tc, reason)
            tc._left(client, reason) # manages notifications of local clients

    def Away(self, uid, msg):
        c = self.Client(uid)
        c.away = msg

    def Notice(self, client, target, msg):
        self.conn.notice(client, target, msg)

    def Privmsg(self, client, target, msg):
        self.conn.privmsg(client, target, msg)

    def addKline(self, kliner, duration, usermask, hostmask, reason):
        pass

    def Kill(self, killer, killee, message):
        if (message is None) or (message == ''):
            message = '<No reason given>'
        qnot = set()
        for chan in killee.chans:
            qnot.update (chan.clients)
            chan.clients.remove(killee)
        for client in qnot:
            client._userQuit(killee, 'Killed (%s (%s))' % (killer.nick, message))
        if killee.onkill:
            killee.onkill(killee)

    def addServer(self, server):
        self.sbysid[server.sid] = server
        self.sbyname[server.name] = server
