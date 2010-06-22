#!/usr/bin/env python

import time
from twisted.internet import reactor, protocol
from twisted.protocols import basic

from ts6.channel import Channel
from ts6.client import Client
from ts6.server import Server

from itertools import islice

def split_every(n, iterable):
    i = iter(iterable)
    piece = list(islice(i, n))
    while piece:
        yield piece
        piece = list(islice(i, n))

class Conn(basic.LineReceiver):
    delimiter = '\n'
    MAX_LENGTH = 16384

    farsid = None
    # incoming message handlers

    def login(self, user, acct):
        user.login = acct
        self.sendLine(':%s ENCAP * SU %s :%s' % (self.state.sid, user.uid, acct))

    def logout(self, user):
        user.login = None
        self.sendLine(':%s ENCAP * SU %s' % (self.state.sid, user.uid))

    def scmode(self, target, modes):
        self.sendLine(':%s TMODE %ld %s %s' % (self.state.sid, target.ts, target.name, modes))

    # 0    1    2    3    4  5     6    7             8 9   10   11      12
    # :sid EUID nick hops ts umode user host(visible) 0 uid host account :gecos
    def got_euid(self, lp, suffix):
        s = self.state.sbysid[lp[0][1:]]
        c = Client(None, s, lp[2],
                   user = lp[6],
                   host = lp[7],
                   hiddenhost = lp[10],
                   gecos = suffix,
                   modes = lp[5],
                   ts = int(lp[4]),
                   login = lp[11],
                   uid = lp[9],
                   )
        self.state.addClient(c)
        self.newClient(c)

    def introduce(self, client):
        """ send EUID and other status for burst """
        self.sendLine(':%s EUID %s 1 %lu %s %s %s 0 %s * * :%s' %
                      (self.state.sid, client.nick, client.ts,
                       client.modes, client.user, client.host, client.uid,
                       client.gecos))
        self.sendLine(':%s ENCAP * IDENTIFIED %s %s' %
                      (self.state.sid, client.uid, client.nick))

    def burstchan(self, channel):
        """ send known channel state for burst """
        print 'bursting channel %s' % (channel,)
        clientchunks = split_every(20, channel.clients)
        for chunk in clientchunks:
            self.sendLine(':%s SJOIN %lu %s + :%s' %
                          (self.state.sid, channel.ts, channel.name, ' '.join(map(lambda x: x.uid, chunk))))

    # :sid UID nick hops ts modes user host ip uid :gecos
    def got_uid(self, lp, suffix):
        s = self.state.sbysid[lp[0][1:]]
        c = Client(None, s, lp[2],
                   user = lp[6],
                   host = lp[7],
                   gecos = suffix,
                   modes = lp[5],
                   ts = int(lp[4]),
                   uid = lp[9],
                   )
        self.state.addClient(c)
        self.newClient(c)

    # :uid QUIT :
    def got_quit(self, lp, suffix):
        uid = lp[0][1:]
        c = self.state.Client(uid)
        c.userQuit(c, suffix)
        self.state.delClient(c)

    # :uid NICK newnick :ts
    def got_nick(self, lp, suffix):
        uid = lp[0][1:]
        newnick = lp[2]
        ts = int(suffix)
        self.state.NickChange(uid, newnick, ts)

    def got_away(self, lp, suffix):
        uid = lp[0][1:]
        self.state.Away(uid, suffix)

    # :00A ENCAP * IDENTIFIED euid nick :OFF
    # :00A ENCAP * IDENTIFIED euid :nick
    # :00A IDENTIFIED euid :nick
    def got_identified(self, lp, suffix):
        uid = lp[2]
        c = self.state.Client(uid)
        c.identified = not ((len(lp) == 3) and (suffix == 'OFF'))

    # PASS theirpw TS 6 :sid
    def got_pass(self, lp, suffix):
        self.farsid = suffix

    def got_capab(self, lp, suffix):
        """ should really handle these as well """
        self.bursting = True
        for c in self.factory.clients:
            c.conn = self
        self.burstStart()
        self.state.conn = self
        self.state.burst()

    # SERVER name hops :gecos
    def got_server(self, lp, suffix):
        s = Server(self.farsid, lp[1], suffix)
        print "Server created: %s" % s
        self.state.sbysid[self.farsid] = s
        self.state.sbyname[lp[1]] = s

    # :upsid SID name hops sid :gecos
    def got_sid(self, lp, suffix):
        s = Server(lp[4], lp[2], suffix)
        self.state.addServer(s)

    def sjoin(self, client, channel):
        if client.server.sid == self.state.sid:
            self.sendLine(':%s SJOIN %lu %s + :@%s' %
                          (client.server.sid, channel.ts, channel.name, client.uid))

    def hack_sjoin(self, client, channel):
        if client.server.sid == self.state.sid:
            channel.tschange(channel.ts - 1, '+')
            self.sjoin(client, channel)

    # :sid SJOIN ts name modes [args...] :uid uid...
    def got_sjoin(self, lp, suffix):
        src = self.findsrc(lp[0][1:])
        (ts, name) = (int(lp[2]), lp[3])

        modes = lp[4:]  ### modes surely aren't in the proper format here
        uids = suffix.split(' ')

        h = self.state.chans.get(name.lower(), None)

        if h:
            if (ts < h.ts):
                # Oops. One of our clients joined a preexisting but split channel
                # and now the split's being healed. Time to do the TS change dance!
                h.tschange(ts, modes)

            elif (ts == h.ts):
                # Merge both sets of modes, since this is 'the same' channel.
                h.modeset(src, modes)

            elif (ts > h.ts):
                # Disregard incoming modes altogether; just use their client list.
                # The far side will take care of kicking remote splitriders if need
                # be.
                pass

        else:
            h = Channel(name, modes, ts)
            self.state.chans[name.lower()] = h

        for x in uids:
            self.state.Join(self.state.Client(x[-9:]), name)

    def join(self, client, channel):
        if client.server.sid == self.state.sid:
            self.sendLine(':%s JOIN %lu %s +' %
                          (client.uid, time.time(), channel.name))

    # :uid JOIN ts name +
    def got_join(self, lp, suffix):
        channel = lp[3]
        client = self.state.Client(lp[0][1:])
        self.state.Join(client, channel)

    def part(self, client, channel, reason=None):
        if reason:
            ir = ' :%s' % reason
        else:
            ir = ''
        if client.server.sid == self.state.sid:
            self.sendLine(':%s PART %s%s' % (client.uid, channel, ir))

    # :uid PART #test :foo
    def got_part(self, lp, suffix):
        if suffix:
            msg = suffix
        else:
            msg = ''
        client = self.state.Client(lp[0][1:])
        channel = lp[2]
        self.state.Part(client, channel, msg)

    # PING :arg
    # :sid PING arg :dest
    def got_ping(self, lp, suffix):
        if lp[0].lower() == 'ping':
            self.sendLine('PONG %s' % lp[1])
            return
        farserv = self.state.sbysid[lp[0][1:]]
        self.sendLine(':%s PONG %s :%s' % (self.factory.me.sid, self.factory.me.name, farserv.sid))

    # SVINFO who cares
    def got_svinfo(self, lp, suffix):
        pass

    # NOTICE
    def got_notice(self, lp, message):
        if self.farsid:
            source = self.uidorchan(lp[0][1:])
            dest = self.uidorchan(lp[2])
            dest.noticed(source, dest, message)

    def got_privmsg(self, lp, message):
        source = self.uidorchan(lp[0][1:])
        dest = self.uidorchan(lp[2])
        dest.privmsg(source, dest, message)

    # ENCAP, argh.
    # :src ENCAP * <cmd [args...]>
    def got_encap(self, line):
        lp = line.split(' ', 4)
        newline = '%s %s %s' % (lp[0], lp[3], lp[4])
        self.dispatch(lp[3], newline)

    # SU
    # :sid SU uid account
    def got_su(self, lp, suffix):
        if len(lp) == 2:
            cuid = suffix
            self.state.Client(cuid).login = None
            self.logoutClient(self.state.Client(cuid))
        else:
            cuid = lp[2]
            self.state.Client(cuid).login = suffix
            self.loginClient(self.state.Client(cuid))

    # :sid MODE uid :+modes
    # :uid MODE uid :+modes
    # charybdis doesn't seem to use the latter two, but I think they're
    # technically legal (charybdis just seems to always use TMODE instead)
    # :sid MODE channel :+modes
    # :uid MODE channel :+modes
    def got_mode(self, lp, modes):
        src = self.findsrc(lp[0][1:])
        if lp[2][0] == '#':
            dest = self.state.chans[lp[2]]
        else:
            dest = self.state.Client(lp[2])
        dest.modeset(src, modes)

    # :sid TMODE ts channel +modes
    # :uid TMODE ts channel +modes
    # yes, TMODE really does not use a ':' before the modes arg.
    def got_tmode(self, lp, suffix):
        modes = lp[4]
        src = self.findsrc(lp[0][1:])
        ts = int(lp[2])
        dest = self.state.chans[lp[3]]
        # We have to discard higher-TS TMODEs because they come from a newer
        # version of the channel.
        if ts > dest.ts:
            print 'TMODE: ignoring higher TS mode %s to %s from %s (%d > %d)' % (
                  modes, dest, src, ts, dest.ts)
            return
        dest.modeset(src, modes)

    # :actinguid KICK channel kickeduid :message
    def got_kick(self, lp, message):
        kicker = self.uidorchan(lp[0][1:])
        channel = self.uidorchan(lp[2])
        kicked = self.uidorchan(lp[3])
        channel.kick(kicker, kicked, message)

    # Interface methods.
    def connectionMade(self):
        self.register()

    def register(self):
        # hardcoded caps :D
        self.sendLine("PASS %s TS 6 :%s" % (self.password, self.state.sid))
        self.sendLine("CAPAB :QS EX IE KLN UNKLN ENCAP TB SERVICES EUID EOPMOD MLOCK")
        self.sendLine("SERVER %s 1 :%s" % (self.state.servername, self.state.serverdesc))
        self.sendLine("SVINFO 6 3 0 :%lu" % int(time.time()))

    # Utility methods

    # findsrc : string -> client-or-server
    # findsrc tries to interpret the provided source in any possible way - first
    # as a SID, then a UID, then maybe a servername, then maybe a nickname.
    def findsrc(self, src):
        if len(src) == 3 and src[0].isdigit() and src.find('.') == -1:
            return self.state.sbysid[src]
        elif len(src) == 9 and src[0].isdigit() and src.find('.') == -1:
            return self.state.Client(src)
        elif src.find('.') != -1:
            return self.state.sbyname[src]
        else:
            return self.state.cbynick[src]

    def uidorchan(self, dst):
        if dst[0] == '#':
            return self.state.chans[dst.lower()]
        else:
            return self.state.Client(dst)

    # Some events

    def sendLine(self, line):
        basic.LineReceiver.sendLine(self, line + '\r')

    def dataReceived(self, data):
        basic.LineReceiver.dataReceived(self, data.replace('\r', ''))

    def dispatch(self, cmd, line):
        method = getattr(self, 'got_%s' % cmd.lower(), None)
        if method is not None:
            t = line.split(' :', 1)
            if len(t) < 2:
                t.append(None)
            method(t[0].split(' '), t[1])
        else:
            print 'Unhandled msg: %s' % line

    def lineReceived(self, line):
        lp = line.split()
        if lp[0].lower() == 'ping':
            self.sendLine('PONG %s' % lp[1])
            if self.bursting:
                self.burstEnd()
                self.bursting = False
            return
        if lp[0][0] != ':':
            lk = lp[0]
        else:
            lk = lp[1]
        if lk.lower() == 'encap':
            self.got_encap(line)
        else:
            self.dispatch(lk, line)

    # Extra interface stuff.
    def newClient(self, client):
        pass

    def loginClient(self, client):
        pass

    def logoutClient(self, client):
        pass

    def burstStart(self):
        pass

    def burstEnd(self):
        pass
