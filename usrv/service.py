from ts6.client import IRCClient

class Service(IRCClient):
    def privmsg(self, src, target, message):
        if target != self:
            pass
        print 'Message: "%s"' % message
        mp = message.split(' ')
        if len(mp) == 1:
            (cp, args) = (message, '')
        else:
            (cp, args) = message.split(' ', 1)
        meth = getattr(self, "cmd_%s" % cp, None)
        if meth:
            meth(src, target, args)
        else:
            self.cmd_unknown(src, target, cp, args)

    def reply(self, src, msg):
        self.notice(src, msg)

    def cmd_unknown(self, src, target, cp, args):
        self.reply(src, 'Unknown command: %s' % cp)
