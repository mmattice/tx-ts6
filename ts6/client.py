#!/usr/bin/env python

import time

from ts6.channel import Channel

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
    def __init__(self, conn, server, nick, *args, **kwargs):
        self.conn = conn
        self.server = server
        self.nick = nick
        self.user = kwargs.get('user', 'twisted')
        self.host = kwargs.get('host', server.name)
        self.hiddenhost = kwargs.get('hiddenhost', server.name)
        if self.hiddenhost == '*':
            self.hiddenhost = self.host
        self.gecos = kwargs.get('gecos', 'twisted-ts6 client')
        self.modes = kwargs.get('modes', 'oS')
        self.login = kwargs.get('login', None)
        if (self.login == '*'):
            self.login = None
        self.ts = kwargs.get('ts', int(time.time()))
        self.chans = []
        if 'uid' in kwargs.keys():
            self.uid = kwargs['uid']
        else:
            self.uid = mkuid()
        self.euid = server.sid + self.uid

    def sendLine(self, line):
        self.conn.sendLine(line)

    def introduce(self):
        self.sendLine(':%s EUID %s 1 %lu %s %s %s 0 %s * * :%s' %
                      (self.conn.me.sid, self.nick, int(time.time()),
                      self.modes, self.user, self.host, self.euid,
                      self.gecos))

    def joined(self, chan):
        self.chans.append(chan)

    def parted(self, chan):
        self.chans.remove(chan)

    # Commands.
    def join(self, channel, key = None):
        tc = self.conn.state.chans.get(channel, None)
        if not tc:
            tc = Channel(channel, 'nt')
            self.conn.state.chans[channel] = tc
        self.sendLine(':%s SJOIN %lu %s + :@%s' %
                      (self.server.sid, int(time.time()), channel, self.euid))
        self.joined(tc)
        tc.joined(self)

    # Hooks
    def userJoined(self, client, channel):
        pass

    def userParted(self, client, channel, message):
        pass

    def userQuit(self, client, message):
        pass
