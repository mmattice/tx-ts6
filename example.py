from ts6.client import Client
from ts6.ircd import IrcdFactory, IrcdConn
from ts6.server import Server

class Idoru(Client):
    def userJoined(self, client, channel):
        Client.userJoined(self, client, channel)
        print '%s: saw join %s %s' % (self.nick, client, channel)

    def joined(self, channel):
        Client.joined(self, channel)
        print '%s: joined %s' % (self.nick, channel)

    def userLeft(self, client, channel, message):
        Client.userLeft(self, client, channel, message)
        print '%s: saw part %s %s "%s"' % (self.nick, client, channel, message)

    def left(self, channel):
        Client.left(self, channel)
        print '%s: left %s' % (self.nick, channel)

    def userQuit(self, client, message):
        Client.userQuit(self, client, message)
        print '%s: saw quit %s "%s"' % (self.nick, client, message)

    def privmsg(self, client, target, message):
        print '%s: saw privmsg %s->%s "%s"' % (self.nick, client, target, message)

    def noticed(self, client, target, message):
        print '%s:  saw notice %s->%s "%s"' % (self.nick, client, target, message)

    def signedOn(self):
        print '%s: signedOn' % (self.nick)
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
        IrcdConn.burstStart(self)

    def burstEnd(self):
        print 'twisted-seven: burst over'

class TestIrcdFactory(IrcdFactory):
    protocol = TestIrcdConn

    def __init__(self):
        self.state.sid = '90B'
        self.state.servername = 'ts6.grixis.local'
        self.me = Server(self.state.sid, self.state.servername, self.state.serverdesc)
        nicks = ('idoru','foo', 'bar', 'baz', 'ack', 'zap', 'kay')
        self.clients = map(lambda x: Idoru(self, self.me, x), nicks)
        for c in self.clients:
            self.state.addClient(c)
            c.connectionMade()

    def clientConnectionLost(self, connector, reason):
        print 'connection lost - %s' % (reason,)
        self.state.cleanNonLocal()
        connector.connect()


from twisted.internet import reactor
reactor.connectTCP('localhost', 5000, TestIrcdFactory())
reactor.run()
