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
    nick = ''
    user = ''
    host = ''
    gecos = ''
    modes = ''

    def __init__(self, server, nick, *args, **kwargs):
        user = 'twisted'
        host = server.name
        gecos = 'twisted-ts6 client'
        if 'user' in kwargs.keys():
            user = kwargs['user']
        if 'host' in kwargs.keys():
            host = kwargs['host']
        if 'gecos' in kwargs.keys():
            gecos = kwargs['gecos']
        if 'uid' in kwargs.keys():
            uid = kwargs['uid']
        else:
            uid = server.sid + mkuid()
