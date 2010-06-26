from usrv.service import Service
import re
import time

authserv = None

class A(Service):
    def __init__(self, factory, server, nick, *args, **kwargs):
        global authserv
        Service.__init__(self, factory, server, nick, *args, **kwargs)
        self.accts = {}
        if not authserv:
            authserv = self
            print 'Authserv: %s' % self

    def isokname(self, name):
        return re.match('^[a-zA-Z0-9_-]+$', name)

    def getacct(self, name):
        return self.accts.get(name.lower(), None)

    def hasflag(self, src, flag):
        a = self.getacct(src.login)
        if not a:
            return False
        return flag in a['flags']

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

    # REGISTER <account> <password>
    def cmd_register(self, src, target, args):
        ap = args.split(' ')
        if len(ap) != 2:
            self.reply(src, 'Syntax: REGISTER <account> <password>')
            return
        (aname, pwd) = ap
        acct = self.getacct(aname)
        if acct:
            self.reply(src, 'Account %s already exists.' % aname)
            return
        if not self.isokname(aname):
            self.reply(src, 'Account name %s is invalid.' % aname)
            return
        self.accts[aname] = {
                                'pwd': pwd,
                                'flags': '',
                                'reg': int(time.time())
                            }
        self.conn.login(src, aname)
        self.reply(src, 'Account %s registered.' % aname)
        if len(self.accts) == 1:
            self.accts[aname]['flags'] = 'ao'
            self.reply(src, 'First account marked as administrator.')

    # LOGIN <account> <password>
    def cmd_login(self, src, target, args):
        ap = args.split(' ')
        if len(ap) != 2:
            self.reply(src, 'Syntax: LOGIN <account> <password>')
            return
        (aname, pwd) = ap
        acct = self.getacct(aname)
        if not acct:
            self.reply(src, 'No account named %s.' % aname)
            return
        if pwd != acct['pwd']:
            self.reply(src, 'Password mismatch.')
            return
        self.conn.login(src, aname)
        self.reply(src, 'You are now logged in as %s.' % aname)

    # INFO <account>
    def cmd_info(self, src, target, args):
        ap = args.split(' ')
        if len(ap) != 1:
            self.reply(src, 'Syntax: INFO <account>')
            return
        ag = self.getacct(ap[0])
        if not ag:
            self.reply(src, 'No account named %s.' % ap[0])
            return
        if ag['flags']:
            fl = ag['flags']
        else:
            fl = '<none>'
        self.reply(src, 'Account %s: flags %s, registered %ld' % (ap[0], fl, ag['reg']))

    # LOGOUT
    def cmd_logout(self, src, target, args):
        if args:
            self.reply(src, 'Syntax: LOGOUT')
            return
        if not src.login:
            self.reply(src, 'You are not logged in.')
            return
        self.conn.logout(src)
        self.reply(src, 'You are now logged out.')

    # DROP
    def cmd_drop(self, src, target, args):
        if args:
            self.reply(src, 'Syntax: DROP')
            return
        if not src.login:
            self.reply(src, 'You are not logged in.')
            return
        del self.accts[src.login.lower()]
        self.conn.logout(src)
        self.reply(src, 'Account deleted.')

    # FLAGS <account> <flags>
    def cmd_flags(self, src, target, args):
        ap = args.split(' ')
        if len(ap) != 2:
            self.reply(src, 'Syntax: FLAGS <account> <flags>')
            return
        if not self.hasflag(src, 'a'):
            self.reply(src, 'Access denied.')
            return
        (acct, flags) = ap
        tu = self.getacct(acct)
        if not tu:
            self.reply(src, 'No account named %s.' % acct)
            return
        (add, remove) = self.parseflags(flags)
        flz = list(tu['flags'])
        for f in add:
            flz.append(f)
        for f in remove:
            flz.remove(f)
        tu['flags'] = ''.join(flz)
        self.reply(src, 'Flags for %s are now %s.' % (acct, tu['flags']))

