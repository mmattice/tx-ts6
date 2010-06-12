#!/usr/bin/env python

nextuid = [ 0, 0, 0, 0, 0, 0 ]
uidchars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
def mkuid():
    uid = nextuid
    for i in range(5, 0, -1):
        if nextuid[i] != (ord('z') - ord('a') + 10):
            nextuid[i] += 1
            break
        nextuid[i] = 0
    return ''.join([uidchars[x] for x in uid])

class Client:
    def __init__(self, server, nick, *args, **kwargs):
        self.nick = nick
        self.user = kwargs.get('user', 'twisted')
        self.host = kwargs.get('host', server.name)
        self.gecos = kwargs.get('gecos', 'twisted-ts6 client')
        self.modes = kwargs.get('modes', 'oS')
        if 'uid' in kwargs.keys():
            self.uid = kwargs['uid']
        else:
            self.uid = server.sid + mkuid()
