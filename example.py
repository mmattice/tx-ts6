from ts6.client import Client
from ts6.ircd import IrcdFactory, IrcdConn
from ts6.server import Server

class Idoru(Client):
    def userJoined(self, client, channel):
        Client.userJoined(self, client, channel)
        print 'Idoru: join %s %s' % (client.nick, channel.name)

    def userParted(self, client, channel, message):
        Client.userParted(self, client, channel, message)
        print 'Idoru: part %s %s "%s"' % (client.nick, channel.name, message)

    def userQuit(self, client, message):
        Client.userQuit(self, client, message)
        print 'Idoru: quit %s "%s"' % (client.nick, message)

    def signedOn(self):
        self.join('#test')

class TestIrcdConn(IrcdConn):
    password = 'acceptpw'
    def sendLine(self, line):
        IrcdConn.sendLine(self,line)
        print '-> %s' % line

    def lineReceived(self, line):
        print '<- %s' % line
        IrcdConn.lineReceived(self, line)

    def newClient(self, client):
        print 'twisted-seven: client %s identified as %s' % (client, client.login)

    def loginClient(self, client):
        print 'twisted-seven: login %s %s' % (client.nick, client.login)

    def burstStart(self):
        print 'twisted-seven: burst starting'
        for c in self.factory.clients:
            c.conn = self
            c.connectionMade()

    def burstEnd(self):
        print 'twisted-seven: burst over'

class TestIrcdFactory(IrcdFactory):
    protocol = TestIrcdConn

    def __init__(self):
        self.state.sid = '90B'
        self.state.servername = 'ts6.grixis.local'
        self.me = Server(self.state.sid, self.state.servername, self.state.serverdesc)
        self.clients = [Idoru(self, self.me, 'idoru')]
        for c in self.clients:
            self.state.addClient(c)

    def clientConnectionLost(self, connector, reason):
        print 'connection lost - %s' % (reason,)
        self.state.cleanNonLocal()
        connector.connect()


from twisted.internet import reactor
reactor.connectTCP('localhost', 5000, TestIrcdFactory())
reactor.run()
