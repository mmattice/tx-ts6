#!/usr/bin/env python

import time

from ts6.channel import Channel

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
            self.uid = self.conn.state.mkuid()
        self.euid = server.sid + self.uid

    def __str__(self):
        return '%s:%s!%s@%s' % (self.euid, self.nick, self.user, self.host)

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

    def modeset(self, src, modes):
        print 'client %s modes: %s' % (self.euid, modes)

    # Commands.
    def join(self, channel, key = None):
        tc = self.conn.state.chans.get(channel, None)
        if not tc:
            tc = Channel(channel, 'nt', int(time.time()))
            self.conn.state.chans[channel] = tc
        self.sendLine(':%s SJOIN %lu %s + :@%s' %
                      (self.server.sid, tc.ts, channel, self.euid))
        self.joined(tc)
        tc.joined(self)

    # Hooks
    def userJoined(self, client, channel):
        pass

    def userParted(self, client, channel, message):
        pass

    def userQuit(self, client, message):
        pass
