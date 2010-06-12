from twisted.internet import protocol

from ts6.conn import Conn
from ts6.client import Client
from ts6.server import Server

class Idoru(Client):
    def introduce(self):
        Client.introduce(self)
        self.join('#test')

    def userJoined(self, client, channel):
        Client.userJoined(self, client, channel)
        print 'Idoru: join %s %s' % (client.nick, channel.name)

class IdoruConn(Conn):
    def connectionMade(self):
        self.password = 'acceptpw'
        self.sid = '90B'
        self.name = 'ts6.grixis.local'
        self.desc = 'twisted-ts6 test'

        Conn.connectionMade(self)
        self.introduce(Idoru(self, self.me, 'idoru'))

    def sendLine(self, line):
        Conn.sendLine(self, line)
        print '-> %s' % line

    def lineReceived(self, line):
        print '<- %s' % line
        Conn.lineReceived(self, line)

    def newClient(self, client):
        print 'Idoru: client %s' % client.nick

    def loginClient(self, client):
        print 'Idoru: login %s %s' % (client.nick, client.login)

class IdoruFactory(protocol.ClientFactory):
    protocol = IdoruConn

from twisted.internet import reactor
reactor.connectTCP('localhost', 5000, IdoruFactory())
reactor.run()
