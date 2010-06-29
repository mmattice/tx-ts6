from ts6.client import TS6Client

class Idoru(TS6Client):
    def userJoined(self, client, channel):
        print '%s: saw join %s %s' % (self.nick, client, channel)

    def joined(self, channel):
        print '%s: joined %s' % (self.nick, channel)

    def userLeft(self, client, channel, message):
        print '%s: saw part %s %s "%s"' % (self.nick, client, channel, message)

    def left(self, channel):
        print '%s: left %s' % (self.nick, channel)

    def userQuit(self, client, message):
        print '%s: saw quit %s "%s"' % (self.nick, client, message)

    def privmsg(self, client, target, message):
        print '%s: saw privmsg %s->%s "%s"' % (self.nick, client, target, message)

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

