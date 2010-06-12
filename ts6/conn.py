#!/usr/bin/env python

import time
from twisted.internet import reactor, protocol
from twisted.protocols import basic

from ts6.server import Server

class Conn(basic.LineReceiver):
    delimiter = '\n'
    MAX_LENGTH = 16384

    def introduce(self, obj):
        obj.introduce(self)

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
