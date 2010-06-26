from usrv.service import Service
from usrv.a import authserv

class C(Service):
    def __init__(self, factory, server, nick, *args, **kwargs):
        Service.__init__(self, factory, server, nick, *args, **kwargs)
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

    def parseflags(self, flags):
        set = True
        add = []
        remove = []
        for f in flags:
            if f == '+':
                set = True
            elif f == '-':
                set = False
            elif set:
                add.append(f)
            else:
                remove.append(f)
        return (add, remove)

    def canchange(self, chan, src, flags):
        if self.hasacs(chan, src, 'f'):
            return True
        if 'f' in flags:
            return False
        return self.hasacs(chan, src, 'a')

    def checkfounders(self, src, cn):
        ch = self.getchan(cn)
        tf = 0
        for x in ch['acl']:
            if 'f' in ch['acl'][x]:
                tf += 1
        if tf != 0:
            return
        self.reply(src, 'Dropping %s (no founders)' % cn)
        del self.chans[cn.lower()]

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
                                        { src.login: 'afjorv' }
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

    # RECOVER <channel>
    def cmd_recover(self, src, target, args):
        ap = args.split(' ')
        if len(ap) != 1:
            self.reply(src, 'Syntax: RECOVER <channel>')
            return
        if not self.hasacs(ap[0], src, 'r'):
            self.reply(src, 'No access.')
            return
        ch = self.conn.state.chans.get(ap[0].lower(), None)
        if not ch:
            self.reply(src, 'Channel %s is empty.' % ap[0])
            return
        self.conn.hack_sjoin(self, ch)
        self.conn.scmode(ch, '+o %s' % src.uid)
        self.conn.part(self, ch, 'RECOVER by %s' % src)
        self.reply(src, 'Channel %s recovered.' % ap[0])

    # FLAGS <channel> [account [flags]]
    def cmd_flags(self, src, target, args):
        ap = args.split(' ')
        if len(ap) < 1:
            self.reply(src, 'Syntax: FLAGS <channel> [account [flags]]')
            return
        ch = self.getchan(ap[0])
        if not ch:
            self.reply(src, 'Channel %s is not registered.' % ap[0])
            return
        if len(ap) == 1:
            ks = ch['acl'].keys()
            ks.sort()
            self.reply(src, 'Flags for %s:' % ap[0])
            for a in ks:
                self.reply(src, '  %s %s' % (a, ch['acl'][a]))
            self.reply(src, 'Done (%d entries)' % len(ks))
            return
        if len(ap) == 2:
            u = ch['acl'].get(ap[1].lower(), '<none>')
            self.reply(src, 'Flags for %s on %s: %s' % (ap[1], ap[0], u))
            return
        if len(ap) == 3:
            if not self.canchange(ap[0], src, ap[2]):
                self.reply(src, 'Access denied.')
                return
            (add, remove) = self.parseflags(ap[2])
            flz = list(ch['acl'].get(ap[1].lower(), ''))
            for f in add:
                flz.append(f)
            for f in remove:
                flz.remove(f)
            flz = ''.join(flz)
            if flz:
                ch['acl'][ap[1].lower()] = flz
                self.reply(src, 'Flags for %s on %s set to %s.' % (ap[1], ap[0], flz))
            else:
                del ch['acl'][ap[1].lower()]
                self.reply(src, 'Flags for %s on %s deleted.' % (ap[1], ap[0]))
            self.checkfounders(src, ap[0])
            return
        self.reply(src, 'Syntax: FLAGS <channel> [account [flags]]')

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
