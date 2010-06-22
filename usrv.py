#!/usr/bin/env python

from ts6.client import Client
from ts6.ircd import IrcdFactory, IrcdConn
from ts6.server import Server

from usrv.a import A
from usrv.c import C

class USrvConn(IrcdConn):
    password = 'acceptpw'

    def sendLine(self, line):
        IrcdConn.sendLine(self, line)
        print '-> %s' % line

    def lineReceived(self, line):
        print '<- %s' % line
        IrcdConn.lineReceived(self, line)

class USrvFactory(IrcdFactory):
    protocol = USrvConn

    def __init__(self):
        self.state.sid = '90B'
        self.state.servername = 'ts6.grixis.local'
        self.state.serverdesc = 'usrv services'
        self.me = Server(self.state.sid, self.state.servername, self.state.serverdesc)
        self.clients = [ A(self, self.me, 'A'), C(self, self.me, 'C') ]
        for c in self.clients:
            self.state.addClient(c)

    def clientConnectionLost(self, connector, reason):
        print 'connection lost: %s' % (reason)
        self.state.cleanNonLocal()
        connector.connect()

from twisted.internet import reactor
reactor.connectTCP('localhost', 5000, USrvFactory())
reactor.run()
