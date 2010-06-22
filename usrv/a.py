from usrv.service import Service
import re

authserv = None

class A(Service):
    def __init__(self, factory, server, nick, *args, **kwargs):
        global authserv
        Service.__init__(self, factory, server, nick, args, kwargs)
        self.accts = {}
        if not authserv:
            authserv = self
            print 'Authserv: %s' % self

    def isokname(self, name):
        return re.match('^[a-zA-Z0-9_-]+$', name)

    def getacct(self, name):
        return self.accts.get(name.lower(), None)

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
        self.accts[aname] = { 'pwd': pwd, 'flags': [] }
        self.conn.login(src, aname)
        self.reply(src, 'Account %s registered.' % aname)

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
