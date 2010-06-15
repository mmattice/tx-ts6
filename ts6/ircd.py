from twisted.internet import protocol

from ts6.conn import Conn
from ts6.server import Server
from ts6.serverstate import ServerState


class IrcdConn(Conn):
    def connectionMade(self):
        self.password = 'acceptpw'
        self.state = self.factory.state

        Conn.connectionMade(self)
        #self.protocol.introduce(Idoru(self, self.me, 'idoru'))

    def sendLine(self, line):
        Conn.sendLine(self, line)
        print '-> %s' % line

    def lineReceived(self, line):
        print '<- %s' % line
        Conn.lineReceived(self, line)

    def newClient(self, client):
        print 'twisted-seven: client %s identified as %s' % (client.nick, client.login)

    def loginClient(self, client):
        print 'twisted-seven: login %s %s' % (client.nick, client.login)

class IrcdFactory(protocol.ClientFactory):
    protocol = IrcdConn
    state = ServerState()
    pseudoclientstate = {}

    def clientConnectionLost(self, connector, reason):
        print 'connection lost - %s' % (reason,)
        self.state.cleanNonLocal()
        connector.connect()

