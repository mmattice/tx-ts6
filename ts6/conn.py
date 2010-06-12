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

    # :sid EUID nick hops ts umode user host 0 uid * * :gecos
    def got_euid(self, line):
        lp = line.split(' ', 13)
        s = self.sbysid[lp[0][1:]]
        c = Client(None, s, lp[2],
                   { 'user': lp[6],
                     'host': lp[7],
                     'gecos': lp[12][1:],
                     'modes': lp[5] })
        self.cbyuid[lp[9]] = c
        self.cbynick[lp[2]] = c
        self.newClient(c)

    # PASS theirpw TS 6 :sid
    def got_pass(self, line):
        lp = line.split(' ', 5)
        self.farsid = lp[4][1:]

    # SERVER name hops :gecos
    def got_server(self, line):
        lp = line.split(' ', 4)
        s = Server(self.farsid, lp[1], lp[3][1:])
        self.sbysid[self.farsid] = s
        self.sbyname[lp[1]] = s

    # :upsid SID name hops sid :gecos
    def got_sid(self, line):
        lp = line.split(' ', 6)
        s = Server(lp[4], lp[2], lp[5][1:])
        self.sbysid[lp[4]] = s
        self.sbyname[lp[2]] = s

    # :sid SJOIN ts name modes :uid uid...
    def got_sjoin(self, line):
        lp = line.split(' ')
        # XXX ignores all the SJOIN cleverness... very broken
        h = self.chans.get(lp[3], None)
        if not h:
            h = Channel(lp[3], lp[4])
        self.chans[lp[3]] = h
        lp[5] = lp[5][1:]

        for x in lp[5:]:
            c = self.cbyuid[x[-9:]]
            c.joined(h)
            h.joined(c)

    # :uid JOIN ts name +
    def got_join(self, line):
        lp = line.split(' ')
        h = self.chans[lp[3]]
        c = self.cbyuid[lp[0][1:]]
        c.joined(h)
        h.joined(c)

    # PING :arg
    # :sid PING arg :dest
    def got_ping(self, line):
        lp = line.split(' ')
        if lp[0].lower() == 'ping':
            self.sendLine('PONG %s' % lp[1])
            return
        farserv = self.sbysid[lp[0][1:]]
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
        cmd = lp[3].lower()
        if cmd not in self.msgs:
            print 'Unhandled ENCAP: %s' % line
            return
        self.msgs[cmd](newline)

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
        self.cbyuid[cuid].login = lp[3]
        if lp[3]:
            self.loginClient(self.cbyuid[cuid])
        else:
            self.logoutClient(self.cbyuid[cuid])

    def __init__(self):
        self.chans = {}
        self.sbysid = {}
        self.sbyname = {}
        self.cbyuid = {}
        self.cbynick = {}
        self.msgs = {
            'su': self.got_su,
            'encap': self.got_encap,
            'sjoin': self.got_sjoin,
            'join': self.got_join,
            'svinfo': self.got_svinfo,
            'notice': self.got_notice,
            'ping': self.got_ping,
            'sid': self.got_sid,
            'euid': self.got_euid,
            'pass': self.got_pass,
            'server': self.got_server,
        }

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

    def lineReceived(self, line):
        lp = line.split()
        if lp[0].lower() == 'ping':
            self.sendLine('PONG %s' % lp[1])
            return
        if lp[0][0] != ':':
            lk = lp[0]
        else:
            lk = lp[1]
        if lk.lower() not in self.msgs:
            print 'Unhandled msg: %s' % line
            return
        self.msgs[lk.lower()](line)

    # Extra interface stuff.
    def newClient(self, client):
        pass

    def loginClient(self, client):
        pass

    def logoutClient(self, client):
        pass
