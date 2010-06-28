from twisted.internet import protocol
from twisted.words.protocols.irc import ServerSupportedFeatures

from ts6.conn import Conn
from ts6.server import Server
from ts6.serverstate import ServerState


class IrcdConn(Conn):
    password = ''

    def connectionMade(self):
        self.state = self.factory.state
        self.state.conn = self
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
    supports = ServerSupportedFeatures()

    def __init__(self):
        self.me = Server(self.state.sid, self.state.servername, self.state.serverdesc)
        self.supports.parse("""
            CHANTYPES=# EXCEPTS INVEX CHANMODES=eIbq,k,flj,CFLMPQScgimnprstz
            CHANLIMIT=#:120 PREFIX=(ov)@+ MAXLIST=bqeI:100 MODES=4
            KNOCK STATUSMSG=@+ CALLERID=g SAFELIST ELIST=U
            CASEMAPPING=rfc1459 CHARSET=ascii NICKLEN=16 CHANNELLEN=50
            TOPICLEN=390 ETRACE CPRIVMSG CNOTICE DEAF=D MONITOR=100 FNC
            TARGMAX=NAMES:1,LIST:1,KICK:1,WHOIS:1,PRIVMSG:4,NOTICE:4,ACCEPT:,MONITOR:
            EXTBAN=$,arx WHOX CLIENTVER=3.0
            """)
