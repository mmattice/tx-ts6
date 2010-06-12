#!/usr/bin/env python

import time
from twisted.internet import reactor, protocol
from twisted.protocols import basic

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
        print 'Client: %s' % lp[2]

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
        print 'Server: %s' % lp[2]

    def __init__(self):
        self.sbysid = {}
        self.sbyname = {}
        self.cbyuid = {}
        self.cbynick = {}
        self.msgs = {
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
        print "-> %s" % line
        basic.LineReceiver.sendLine(self, line + '\r')

    def dataReceived(self, data):
        basic.LineReceiver.dataReceived(self, data.replace('\r', ''))

    def lineReceived(self, line):
        print "<- %s" % line
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
