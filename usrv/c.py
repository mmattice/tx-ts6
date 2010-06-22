from usrv.service import Service
from usrv.a import authserv

class C(Service):
    def __init__(self, factory, server, nick, *args, **kwargs):
        Service.__init__(self, factory, server, nick, args, kwargs)
        self.chans = {}
    
    def getchan(self, name):
        return self.chans.get(name.lower(), None)

    def hasacs(self, cn, user, ac):
        c = self.getchan(cn)
        if not c:
            return False
        if not user.login:
            return False
        if not user.login in c['acl']:
            return False
        return ac in c['acl'][user.login]

    # REGISTER <channel>
    def cmd_register(self, src, target, args):
        ap = args.split(' ')
        if len(ap) != 1:
            self.reply(src, 'Syntax: REGISTER <channel>')
            return
        if not src.login:
            self.reply(src, 'You are not logged in.')
            return
        if self.getchan(ap[0]):
            self.reply(src, 'Channel %s is already registered.' % ap[0])
            return
        exc = self.conn.state.chans.get(ap[0].lower(), None)
        if not exc:
            self.reply(src, 'Channel %s does not exist.' % ap[0])
            return
        self.chans[ap[0].lower()] = { 'acl':
                                        { src.login: 'afjov' }
                                    }
        self.reply(src, 'Channel %s registered.' % ap[0])

    # DROP <channel>
    def cmd_drop(self, src, target, args):
        ap = args.split(' ')
        if len(ap) != 1:
            self.reply(src, 'Syntax: DROP <channel>')
            return
        if not self.hasacs(ap[0], src, 'f'):
            self.reply(src, 'No access.')
            return
        del self.chans[ap[0].lower()]
        self.reply(src, 'Channel %s dropped.' % ap[0])


    # mode command backend
    def modecmd(self, src, args, flag, mode, name):
        ap = args.split(' ')
        if len(ap) != 2:
            self.reply(src, 'Syntax: %s <channel> <nick>' % name)
            return
        (chan, nick) = ap
        if not self.hasacs(chan, src, flag):
            self.reply(src, 'No access.')
            return
        user = self.conn.state.cbynick.get(nick.lower(), None)
        if not user:
            self.reply(src, 'No client named %s.' % user)
            return
        ch = self.conn.state.chans.get(chan.lower(), None)
        if not ch:
            self.reply(src, '%s is empty.' % ch)
            return
        self.conn.scmode(ch, '%s %s' % (mode, user.uid))
        self.reply(src, 'Set mode %s %s on %s.' % (mode, nick, chan))

    def cmd_op(self, src, target, args):
        return self.modecmd(src, args, 'o', '+o', 'OP')

    def cmd_deop(self, src, target, args):
        return self.modecmd(src, args, 'o', '-o', 'DEOP')

    def cmd_voice(self, src, target, args):
        return self.modecmd(src, args, 'v', '+v', 'VOICE')

    def cmd_devoice(self, src, target, args):
        return self.modecmd(src, args, 'v', '-v', 'DEVOICE')
