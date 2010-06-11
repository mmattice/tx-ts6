#!/usr/bin/env python

import time
from twisted.internet import reactor, protocol
from twisted.protocols import basic

class TS6(basic.LineReceiver):
    delimiter = '\n'
    MAX_LENGTH = 16384

    nextuid = 0

    def mkuid(self):
        # LOL STUB
        return self.numeric + 'AAAAAI'

    def introduceClient(self, nick, user, host, gecos):
        # LOL STUB - always sends +oS as user modes. Needs to deal with actual
        # 'user' objects, I think.
        self.sendLine(":%s EUID %s 1 %lu oS %s %s 0 %s * * :%s" %
            (self.numeric, nick, int(time.time()), user, host, self.mkuid(), gecos))

    # Interface methods.
    def connectionMade(self):
        self.register()

    def register(self):
        # hardcoded caps :D
        self.sendLine("PASS %s TS 6 :%s" % (self.password, self.numeric))
        self.sendLine("CAPAB :QS EX IE KLN UNKLN ENCAP TB SERVICES EUID EOPMOD MLOCK")
        self.sendLine("SERVER %s 1 :%s" % (self.name, self.desc))
        self.sendLine("SVINFO 6 3 0 :%lu" % int(time.time()))

    def sendLine(self, line):
        basic.LineReceiver.sendLine(self, line + '\r')

    def dataReceived(self, data):
        basic.LineReceiver.dataReceived(self, data.replace('\r', ''))

    def lineReceived(self, line):
        print "Line: %s" % line

class TS6Factory(protocol.ClientFactory):
    def startedConnecting(self, connector):
        print "Connect..."

    def buildProtocol(self, addr):
        print "Connected."
        return TS6()
