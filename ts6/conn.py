#!/usr/bin/env python

import time
from twisted.internet import reactor, protocol
from twisted.protocols import basic

from ts6.channel import Channel
from ts6.client import Client
from ts6.server import Server

class Conn(basic.LineReceiver):
    delimiter = '\n'
    MAX_LENGTH = 16384

    # incoming message handlers

    # 0    1    2    3    4  5     6    7             8 9   10   11      12
    # :sid EUID nick hops ts umode user host(visible) 0 uid host account :gecos
    def got_euid(self, line):
        lp = line.split(' ', 13)
        s = self.state.sbysid[lp[0][1:]]
        c = Client(None, s, lp[2],
                   user = lp[6],
                   host = lp[7],
                   hiddenhost = lp[10],
                   gecos = lp[12][1:],
                   modes = lp[5],
                   ts = int(lp[4]),
                   login = lp[11],
                   uid = lp[9],
                   )
        self.state.cbyuid[lp[9]] = c
        self.state.cbynick[lp[2].lower()] = c
        self.newClient(c)

    # :sid UID nick hops ts modes user host ip uid :gecos
    def got_uid(self, line):
        lp = line.split(' ', 11)
        s = self.state.sbysid[lp[0][1:]]
        c = Client(None, s, lp[2],
                   user = lp[6],
                   host = lp[7],
                   gecos = lp[10][1:],
                   modes = lp[5],
                   ts = int(lp[4]),
                   uid = lp[9],
                   )
        self.state.cbyuid[lp[9]] = c
        self.state.cbynick[lp[2].lower()] = c
        self.newClient(c)

    # :20QAAAAAC QUIT :
    def got_quit(self, line):
        lp = line.split(' ', 3)
        uid = lp[0][1:]
        c = self.state.cbyuid[uid]
        c.userQuit(c, lp[2][1:])
        del(self.state.cbynick[c.nick.lower()])
        del(self.state.cbyuid[uid])

    # :uid NICK newnick :ts
    def got_nick(self, line):
        lp = line.split(' ', 4)
        uid = lp[0][1:]
        newnick = lp[2]
        c = self.state.cbyuid[uid]
        oldnick = c.nick
        self.state.cbynick[newnick.lower()] = self.state.cbynick.pop(oldnick.lower())
        c.nick = newnick
        c.ts = int(lp[3][1:])
        c.identified = False

    # :00A ENCAP * IDENTIFIED euid nick :OFF
    # :00A ENCAP * IDENTIFIED euid :nick
    # :00A IDENTIFIED euid :nick
    def got_identified(self, line):
        lp = line.split(' ')
        uid = lp[2]
        c = self.state.cbyuid[uid]
        if (len(lp) == 7) and (lp[-1] == ':OFF'):
            c.identified = False
        else:
            c.identified = True

    # PASS theirpw TS 6 :sid
    def got_pass(self, line):
        lp = line.split(' ', 5)
        self.farsid = lp[4][1:]

    # SERVER name hops :gecos
    def got_server(self, line):
        lp = line.split(' ', 4)
        s = Server(self.farsid, lp[1], lp[3][1:])
        self.state.sbysid[self.farsid] = s
        self.state.sbyname[lp[1]] = s

    # :upsid SID name hops sid :gecos
    def got_sid(self, line):
        lp = line.split(' ', 6)
        s = Server(lp[4], lp[2], lp[5][1:])
        self.state.sbysid[lp[4]] = s
        self.state.sbyname[lp[2]] = s

    # :sid SJOIN ts name modes :uid uid...
    def got_sjoin(self, line):
        lp = line.split(' ')
        # XXX ignores all the SJOIN cleverness... very broken
        h = self.state.chans.get(lp[3], None)
        if not h:
            h = Channel(lp[3], lp[4])
        self.state.chans[lp[3]] = h
        lp[5] = lp[5][1:]

        for x in lp[5:]:
            c = self.state.cbyuid[x[-9:]]
            c.joined(h)
            h.joined(c)

    # :uid JOIN ts name +
    def got_join(self, line):
        lp = line.split(' ')
        h = self.state.chans[lp[3]]
        c = self.state.cbyuid[lp[0][1:]]
        c.joined(h)
        h.joined(c)

    # :20QAAAAAB PART #test :foo
    def got_part(self, line):
        lp = line.split(' ', 4)
        if len(lp) == 4:
            msg = lp[3][1:]
        else:
            msg = ''
        h = self.state.chans[lp[2]]
        c = self.state.cbyuid[lp[0][1:]]
        c.parted(h)
        h.parted(c, msg)

    # PING :arg
    # :sid PING arg :dest
    def got_ping(self, line):
        lp = line.split(' ')
        if lp[0].lower() == 'ping':
            self.sendLine('PONG %s' % lp[1])
            return
        farserv = self.state.sbysid[lp[0][1:]]
        self.sendLine(':%s PONG %s :%s' % (self.me.sid, self.me.name, farserv.sid))

    # SVINFO who cares
    def got_svinfo(self, line):
        pass

    # NOTICE
    def got_notice(self, line):
        pass

    # ENCAP, argh.
    # :src ENCAP * <cmd [args...]>
    def got_encap(self, line):
        lp = line.split(' ', 4)
        newline = '%s %s %s' % (lp[0], lp[3], lp[4])
        self.dispatch(lp[3], newline)

    # SU
    # :sid SU uid account
    def got_su(self, line):
        print 'SU: %s' % line
        lp = line.split(' ')
        cuid = lp[2]
        if cuid[0] == ':':
            cuid = cuid[1:]
        if len(lp) <= 3:
            lp.append(None)
        self.state.cbyuid[cuid].login = lp[3]
        if lp[3]:
            self.loginClient(self.state.cbyuid[cuid])
        else:
            self.logoutClient(self.state.cbyuid[cuid])

    def introduce(self, obj):
        obj.introduce()

    # Interface methods.
    def connectionMade(self):
        self.me = Server(self.sid, self.name, self.desc)
        self.register()

    def register(self):
        # hardcoded caps :D
        self.sendLine("PASS %s TS 6 :%s" % (self.password, self.sid))
        self.sendLine("CAPAB :QS EX IE KLN UNKLN ENCAP TB SERVICES EUID EOPMOD MLOCK")
        self.sendLine("SERVER %s 1 :%s" % (self.name, self.desc))
        self.sendLine("SVINFO 6 3 0 :%lu" % int(time.time()))

    def sendLine(self, line):
        basic.LineReceiver.sendLine(self, line + '\r')

    def dataReceived(self, data):
        basic.LineReceiver.dataReceived(self, data.replace('\r', ''))

    def dispatch(self, cmd, line):
        method = getattr(self, 'got_%s' % cmd.lower(), None)
        if method is not None:
            method(line)
        else:
            print 'Unhandled msg: %s' % line

    def lineReceived(self, line):
        lp = line.split()
        if lp[0].lower() == 'ping':
            self.sendLine('PONG %s' % lp[1])
            return
        if lp[0][0] != ':':
            lk = lp[0]
        else:
            lk = lp[1]
        self.dispatch(lk, line)

    # Extra interface stuff.
    def newClient(self, client):
        pass

    def loginClient(self, client):
        pass

    def logoutClient(self, client):
        pass
