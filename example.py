from ts6.client import IRCClient, TS6Client
from ts6.ircd import IrcdFactory, IrcdConn
from ts6.server import Server

class Idoru(IRCClient):
    def userJoined(self, client, channel):
        IRCClient.userJoined(self, client, channel)
        print '%s: saw join %s %s' % (self.nick, client, channel)

    def joined(self, channel):
        IRCClient.joined(self, channel)
        print '%s: joined %s' % (self.nick, channel)

    def userLeft(self, client, channel, message):
        IRCClient.userLeft(self, client, channel, message)
        print '%s: saw part %s %s "%s"' % (self.nick, client, channel, message)

    def left(self, channel):
        IRCClient.left(self, channel)
        print '%s: left %s' % (self.nick, channel)

    def userQuit(self, client, message):
        IRCClient.userQuit(self, client, message)
        print '%s: saw quit %s "%s"' % (self.nick, client, message)

    def privmsg(self, client, target, message):
        print '%s: saw privmsg %s->%s "%s"' % (self.nick, client, target, message)
        if (target[0] == '#') and ('cycle' in message):
            self.part(target)
            self.join(target)
        elif ('ts6' not in client):
            try:
                if ('@' in target):
                    self.msg(client.split('!')[0], message)
                else:
                    self.msg(target, message)
            except Exception, msg:
                print 'Idoru.privmsg failed %s - %s' % (Exception, msg)


    def noticed(self, client, target, message):
        print '%s:  saw notice %s->%s "%s"' % (self.nick, client, target, message)

    def kickedFrom(self, channel, kicker, message):
        print '%s was kicked from %s by %s "%s"' % (self, channel, kicker, message)
        self.join(channel)

    def userKicked(self, kickee, channel, kicker, message):
        print '%s: saw %s kick %s from %s "%s"' % (self, kicker, kickee, channel, message)

    def signedOn(self):
        print '%s: signedOn' % (self.nick)
        self.join('#test')

    def userRenamed(self, oldnick, newnick):
        print '%s: saw %s /nick to %s' % (self, oldnick, newnick)

class NewIdoru(TS6Client):
    def userJoined(self, client, channel):
        TS6Client.userJoined(self, client, channel)
        print '%s: saw join %s %s' % (self.nick, client, channel)

    def joined(self, channel):
        TS6Client.joined(self, channel)
        print '%s: joined %s' % (self.nick, channel)

    def userLeft(self, client, channel, message):
        TS6Client.userLeft(self, client, channel, message)
        print '%s: saw part %s %s "%s"' % (self.nick, client, channel, message)

    def left(self, channel):
        TS6Client.left(self, channel)
        print '%s: left %s' % (self.nick, channel)

    def userQuit(self, client, message):
        TS6Client.userQuit(self, client, message)
        print '%s: saw quit %s "%s"' % (self.nick, client, message)

    def privmsg(self, client, target, message):
        print '%s: saw privmsg %s->%s "%s"' % (self.nick, client, target, message)
        if (target[0] == '#') and ('cycle' in message):
            self.part(target)
            self.join(target)
        elif ('ts6' not in client):
            try:
                if ('@' in target):
                    self.msg(client.nick, message)
                else:
                    self.msg(target, message)
            except Exception, msg:
                print 'Idoru.privmsg failed %s - %s' % (Exception, msg)

    def noticed(self, client, target, message):
        print '%s:  saw notice %s->%s "%s"' % (self.nick, client, target, message)

    def kickedFrom(self, channel, kicker, message):
        print '%s was kicked from %s by %s "%s"' % (self, channel, kicker, message)
        self.join(channel.name)

    def userKicked(self, kickee, channel, kicker, message):
        print '%s: saw %s kick %s from %s "%s"' % (self, kicker, kickee, channel, message)

    def signedOn(self):
        print '%s: signedOn' % (self.nick)
        self.join('#test')

    def userRenamed(self, oldnick, client):
        print '%s: saw %s(%s) /nick to %s' % (self, oldnick, client.login, client.nick)

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
        self.clients = map(lambda x: Idoru(self, self.me, x, modes = 'oS'), nicks)
        self.clients.append(NewIdoru(self, self.me, 'ts6idoru', modes = 'oS'))
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
