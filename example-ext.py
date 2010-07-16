from ts6.client import Client
from ts6.ircd import IrcdFactory, IrcdConn
from ts6.server import Server

import os
from fnmatch import filter as fnfilter
import yaml
import sys

class TestIrcdConn(IrcdConn):
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

def dyn_load(loadpath):
    try:
        chunks = loadpath.split('.')
        module = __import__('.'.join(chunks[0:-1]), fromlist=[chunks[-1]])
        return getattr(module,chunks[-1])
    except (ImportError, AttributeError):
        print('Cannot load',loadpath)

def get_clients():
    """
    Returns a list of filenames(modules) in clients/ minus the .py extension
    """
    cmps = []
    modules = fnfilter(os.listdir('clients'), '*.py')
    modules.remove('__init__.py')
    cmps.extend(map(lambda x: os.path.splitext(x)[0], modules))
    return cmps

def load_client(name):
    """
    Returns Bot class from client/>name<.py
    """
    if 'clients.%s' % name in sys.modules:
        del(sys.modules['clients.%s' % name])
    return dyn_load('clients.%s.Bot' % (name,))
    
class TestIrcdFactory(IrcdFactory):
    protocol = TestIrcdConn

    def __init__(self, config):
        self.state.sid = config['sid']
        self.state.servername = config['servername']
        self.state.serverdesc = config['serverdesc']
        self.connectpass = config['password']
        self.me = Server(self.state.sid, self.state.servername, self.state.serverdesc)
        clist = get_clients()
        self.clients = {}
        for name in clist:
            cl = load_client(name)
            self.clients[name] = [ cl, cl(self, self.me, name) ]
        for nick, rec in self.clients.iteritems():
            c = rec[1]
            c.onkill = self.reloadClient
            self.state.addClient(c)
            c.connectionMade()

    def reloadClient(self, client):
        for nick, rec in self.clients.iteritems():
            if client == rec[1]:
                print 'reloadClient called on %s' % (client,)
                self.state.delClient(rec[1])
                rec[0] = load_client(nick)
                c = rec[0](self, self.me, nick)
                rec[1] = c
                c.onkill = self.reloadClient
                c.conn = self.state.conn
                self.state.addClient(c)
                c.connectionMade()

    def clientConnectionLost(self, connector, reason):
        print 'connection lost - %s' % (reason,)
        self.state.cleanNonLocal()
        reactor.callLater(10, connector.connect)

    def buildProtocol(self, addr):
        p = self.protocol()
        p.factory = self
        p.password = self.connectpass
        return p

try:
    config = yaml.load(file('example.conf'))
except:
    config = {'host' : 'localhost',
              'port' : 5000,
              'sid'  : '99Z',
              'servername' : 'ts6.',
              'serverdesc' : 'TS6 pseudo server',
              'password' : 'acceptpw',
              }

from twisted.internet import reactor, ssl
if config.get('ssl', False):
    reactor.connectSSL(config['host'], config['port'], TestIrcdFactory(config), ssl.ClientContextFactory())
else:
    reactor.connectTCP(config['host'], config['port'], TestIrcdFactory(config))
reactor.run()
