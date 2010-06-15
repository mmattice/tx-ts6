from twisted.internet import protocol

from ts6.conn import Conn
from ts6.server import Server
from ts6.serverstate import ServerState


class IrcdConn(Conn):
    password = ''

    def connectionMade(self):
        self.state = self.factory.state
        Conn.connectionMade(self)

    def sendLine(self, line):
        Conn.sendLine(self, line)

    def lineReceived(self, line):
        Conn.lineReceived(self, line)

    def newClient(self, client):
        pass

    def loginClient(self, client):
        pass

class IrcdFactory(protocol.ClientFactory):
    protocol = IrcdConn
    state = ServerState()
    pseudoclientstate = {}
