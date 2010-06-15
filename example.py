from ts6.client import Client
from ts6.ircd import IrcdFactory

class Idoru(Client):
    def introduce(self):
        Client.introduce(self)
        self.join('#test')

    def userJoined(self, client, channel):
        Client.userJoined(self, client, channel)
        print 'Idoru: join %s %s' % (client.nick, channel.name)

    def userParted(self, client, channel, message):
        Client.userParted(self, client, channel, message)
        print 'Idoru: part %s %s "%s"' % (client.nick, channel.name, message)

    def userQuit(self, client, message):
        Client.userQuit(self, client, message)
        print 'Idoru: quit %s "%s"' % (client.nick, message)

class TestIrcdFactory(IrcdFactory):
    def __init__(self):
        self.state.sid = '90B'
        self.state.servername = 'ts6.grixis.local'


from twisted.internet import reactor
reactor.connectTCP('localhost', 5000, TestIrcdFactory())
reactor.run()
