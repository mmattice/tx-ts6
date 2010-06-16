#!/usr/bin/env python

import time
from twisted.internet import reactor, protocol
from twisted.protocols import basic

from ts6.channel import Channel
from ts6.client import Client
from ts6.server import Server

class Conn(basic.LineReceiver):
    delimiter = '\n'
    MAX_LENGTH = 16384

    # incoming message handlers

    # 0    1    2    3    4  5     6    7             8 9   10   11      12
    # :sid EUID nick hops ts umode user host(visible) 0 uid host account :gecos
    def got_euid(self, line):
        lp = line.split(' ', 13)
        s = self.state.sbysid[lp[0][1:]]
        c = Client(None, s, lp[2],
                   user = lp[6],
                   host = lp[7],
                   hiddenhost = lp[10],
                   gecos = lp[12][1:],
                   modes = lp[5],
                   ts = int(lp[4]),
                   login = lp[11],
                   uid = lp[9],
                   )
        self.state.addClient(c)
        self.newClient(c)

    # :sid UID nick hops ts modes user host ip uid :gecos
    def got_uid(self, line):
        lp = line.split(' ', 11)
        s = self.state.sbysid[lp[0][1:]]
        c = Client(None, s, lp[2],
                   user = lp[6],
                   host = lp[7],
                   gecos = lp[10][1:],
                   modes = lp[5],
                   ts = int(lp[4]),
                   uid = lp[9],
                   )
        self.state.addClient(c)
        self.newClient(c)

    # :20QAAAAAC QUIT :
    def got_quit(self, line):
        lp = line.split(' ', 3)
        uid = lp[0][1:]
        c = self.state.Client(uid)
        c.userQuit(c, lp[2][1:])
        self.state.delClient(c)

    # :uid NICK newnick :ts
    def got_nick(self, line):
        lp = line.split(' ', 4)
        uid = lp[0][1:]
        newnick = lp[2]
        ts = int(lp[3][1:])
        self.state.NickChange(uid, newnick, ts)

    # :00A ENCAP * IDENTIFIED euid nick :OFF
    # :00A ENCAP * IDENTIFIED euid :nick
    # :00A IDENTIFIED euid :nick
    def got_identified(self, line):
        lp = line.split(' ')
        uid = lp[2]
        c = self.state.Client(uid)
        if (len(lp) == 7) and (lp[-1] == ':OFF'):
            c.identified = False
        else:
            c.identified = True

    # PASS theirpw TS 6 :sid
    def got_pass(self, line):
        lp = line.split(' ', 5)
        self.farsid = lp[4][1:]

    # SERVER name hops :gecos
    def got_server(self, line):
        lp = line.split(' ', 4)
        s = Server(self.farsid, lp[1], lp[3][1:])
        self.state.sbysid[self.farsid] = s
        self.state.sbyname[lp[1]] = s

    # :upsid SID name hops sid :gecos
    def got_sid(self, line):
        lp = line.split(' ', 6)
        s = Server(lp[4], lp[2], lp[5][1:])
        self.state.addServer(s)

    # :sid SJOIN ts name modes [args...] :uid uid...
    def got_sjoin(self, line):
        lp = line.split(' ')
        src = self.findsrc(lp[0][1:])
        (ts, name) = (int(lp[2]), lp[3])

        modes = []
        uids = lp[4:]
        while uids:
            m = uids[0]
            if m[0] == ':':
                break
            modes.append(m)
            uids = uids[1:]

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

        uids[0] = uids[0][1:]
        for x in uids:
            self.state.Join(x[-9:], name)

    # :uid JOIN ts name +
    def got_join(self, line):
        lp = line.split(' ')
        channel = lp[3]
        uid = lp[0][1:]
        self.state.Join(uid, channel)

    # :20QAAAAAB PART #test :foo
    def got_part(self, line):
        lp = line.split(' ', 4)
        if len(lp) == 4:
            msg = lp[3][1:]
        else:
            msg = ''
        uid = lp[0][1:]
        channel = lp[2]
        self.state.Part(uid, channel, msg)

    # PING :arg
    # :sid PING arg :dest
    def got_ping(self, line):
        lp = line.split(' ')
        if lp[0].lower() == 'ping':
            self.sendLine('PONG %s' % lp[1])
            return
        farserv = self.state.sbysid[lp[0][1:]]
        self.sendLine(':%s PONG %s :%s' % (self.me.sid, self.me.name, farserv.sid))

    # SVINFO who cares
    def got_svinfo(self, line):
        pass

    # NOTICE
    def got_notice(self, line):
        pass

    # ENCAP, argh.
    # :src ENCAP * <cmd [args...]>
    def got_encap(self, line):
        lp = line.split(' ', 4)
        newline = '%s %s %s' % (lp[0], lp[3], lp[4])
        self.dispatch(lp[3], newline)

    # SU
    # :sid SU uid account
    def got_su(self, line):
        print 'SU: %s' % line
        lp = line.split(' ')
        cuid = lp[2]
        if cuid[0] == ':':
            cuid = cuid[1:]
        if len(lp) <= 3:
            lp.append(None)
        self.state.Client(cuid).login = lp[3]
        if lp[3]:
            self.loginClient(self.state.Client(cuid))
        else:
            self.logoutClient(self.state.Client(cuid))

    # :sid MODE uid :+modes
    # :uid MODE uid :+modes
    # charybdis doesn't seem to use the latter two, but I think they're
    # technically legal (charybdis just seems to always use TMODE instead)
    # :sid MODE channel :+modes
    # :uid MODE channel :+modes
    def got_mode(self, line):
        lp = line.split(' ', 4)
        modes = lp[3][1:]
        src = self.findsrc(lp[0][1:])
        if lp[2][0] == '#':
            dest = self.state.chans[lp[2]]
        else:
            dest = self.state.Client(lp[2])
        dest.modeset(src, modes)

    # :sid TMODE ts channel +modes
    # :uid TMODE ts channel +modes
    # yes, TMODE really does not use a ':' before the modes arg.
    def got_tmode(self, line):
        lp = line.split(' ', 5)
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

    def introduce(self, obj):
        obj.introduce()

    # Interface methods.
    def connectionMade(self):
        self.me = Server(self.state.sid, self.state.servername, self.state.serverdesc)
        self.register()
        self.bursting = True
        self.burstStart()

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

    # Some events

    def sendLine(self, line):
        basic.LineReceiver.sendLine(self, line + '\r')

    def dataReceived(self, data):
        basic.LineReceiver.dataReceived(self, data.replace('\r', ''))

    def dispatch(self, cmd, line):
        method = getattr(self, 'got_%s' % cmd.lower(), None)
        if method is not None:
            method(line)
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
