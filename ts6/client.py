#!/usr/bin/env python

import time

from twisted.words.protocols.irc import ctcpExtract, ctcpStringify
from ts6.channel import Channel


class Client:
    def __init__(self, server, nick, *args, **kwargs):
        self.conn = None
        self.server = server
        self.nick = nick
        if 'defaults' not in kwargs:
            kwargs['defaults'] = {}
        for arg in ('user','host','hiddenhost','gecos','modes','login','ts','uid'):
            setattr(self, arg, kwargs.get(arg, kwargs['defaults'].get(arg, None)))
        if self.hiddenhost == '*':
            self.hiddenhost = self.host
        if (self.login == '*'):
            self.login = None
        self.chans = []
        self.onkill = None
        self.identified = False
        self.oper = False

    def __str__(self):
        return '%s!%s@%s' % (self.nick, self.user, self.host)

    ### useful stuff
    def getNick(self, mask):
        return mask.split('!')[0]

    ### Interface level client->user output methods
    ###
    ### You'll want to override these.

    ### Methods relating to the server itself

    def created(self, when):
        """Called with creation date information about the server, usually at logon.

        @type when: C{str}
        @param when: A string describing when the server was created, probably.
        """

    def yourHost(self, info):
        """Called with daemon information about the server, usually at logon.

        @type info: C{str}
        @param when: A string describing what software the server is running, probably.
        """

    def myInfo(self, servername, version, umodes, cmodes):
        """Called with information about the server, usually at logon.

        @type servername: C{str}
        @param servername: The hostname of this server.

        @type version: C{str}
        @param version: A description of what software this server runs.

        @type umodes: C{str}
        @param umodes: All the available user modes.

        @type cmodes: C{str}
        @param cmodes: All the available channel modes.
        """

    def luserClient(self, info):
        """Called with information about the number of connections, usually at logon.

        @type info: C{str}
        @param info: A description of the number of clients and servers
        connected to the network, probably.
        """

    def bounce(self, info):
        """Called with information about where the client should reconnect.

        @type info: C{str}
        @param info: A plaintext description of the address that should be
        connected to.
        """

    def isupport(self, options):
        """Called with various information about what the server supports.

        @type options: C{list} of C{str}
        @param options: Descriptions of features or limits of the server, possibly
        in the form "NAME=VALUE".
        """

    def luserChannels(self, channels):
        """Called with the number of channels existant on the server.

        @type channels: C{int}
        """

    def luserOp(self, ops):
        """Called with information about the server connected to.

        @type info: C{str}
        @param info: A plaintext string describing the number of users and servers
        connected to this server.
        """

    def luserMe(self, info):
        """Called with information about the server connected to.

        @type info: C{str}
        @param info: A plaintext string describing the number of users and servers
        connected to this server.
        """

    ### Internal methods
    def _privmsg(self, source, dest, message):
        """
        Called when we recieve a PRIVMSG

        @type source: C{Client}
        @param source: A Client object referring to the sender of the message

        @type dest: C{Client} or C{Channel}
        @param dest: A Client or Channel object referring to the destination of the message

        @type message: C{str}
        @param message: The message sent

        """

    def _noticed(self, source, dest, message):
        """
        Called when we recieve a NOTICE

        @type source: C{Client}
        @param source: A Client object referring to the sender of the message

        @type dest: C{Client} or C{Channel}
        @param dest: A Client or Channel object referring to the destination of the message

        @type message: C{str}
        @param message: The message sent

        """


    def _left(self, channel):
        self.chans.remove(channel)
        self.left(channel)

    def _joined(self, channel):
        self.chans.append(channel)
        self.joined(channel)

    def _kickedFrom(self, channel, kicker, message):
        self.chans.remove(channel)
        self.kickedFrom(channel, kicker, message)

    ### Methods involving me directly

    def privmsg(self, user, channel, message):
        """Called when I have a message from a user to me or a channel.
        """

    def joined(self, channel):
        """
        Called when I finish joining a channel.

        channel has the starting character (C{'#'}, C{'&'}, C{'!'}, or C{'+'})
        intact.
        """

    def left(self, channel):
        """
        Called when I have left a channel.

        channel has the starting character (C{'#'}, C{'&'}, C{'!'}, or C{'+'})
        intact.
        """

    def noticed(self, user, channel, message):
        """Called when I have a notice from a user to me or a channel.

        By default, this is equivalent to IRCClient.privmsg, but if your
        client makes any automated replies, you must override this!
        From the RFC::

            The difference between NOTICE and PRIVMSG is that
            automatic replies MUST NEVER be sent in response to a
            NOTICE message. [...] The object of this rule is to avoid
            loops between clients automatically sending something in
            response to something it received.
        """

    def pong(self, user, secs):
        """Called with the results of a CTCP PING query.
        """

    def signedOn(self):
        """Called after sucessfully signing on to the server.
        """

    def kickedFrom(self, channel, kicker, message):
        """Called when I am kicked from a channel.
        """

    def nickChanged(self, nick):
        """Called when my nick has been changed.
        """

    ### Things I observe other people doing in a channel.

    def userJoined(self, user, channel):
        """Called when I see another user joining a channel.
        """

    def userLeft(self, user, channel, reason=None):
        """Called when I see another user leaving a channel.
        """

    def userQuit(self, user, quitMessage):
        """Called when I see another user disconnect from the network.
        """

    def userKicked(self, kickee, channel, kicker, message):
        """Called when I observe someone else being kicked from a channel.
        """

    def action(self, user, channel, data):
        """Called when I see a user perform an ACTION on a channel.
        """

    def topicUpdated(self, user, channel, newTopic):
        """In channel, user changed the topic to newTopic.

        Also called when first joining a channel.
        """

    def userRenamed(self, oldname, newname):
        """A user changed their name from oldname to newname.
        """

    ### Information from the server.

    def receivedMOTD(self, motd):
        """I received a message-of-the-day banner from the server.

        motd is a list of strings, where each string was sent as a seperate
        message from the server. To display, you might want to use::

            '\\n'.join(motd)

        to get a nicely formatted string.
        """

    ### user input commands, client->server
    ### Your client will want to invoke these.
    ### These should not be overriden without careful consideration

    def join(self, channel, key=None):
        """
        Join a channel.

        @type channel: C{str}
        @param channel: The name of the channel to join. If it has no prefix,
            C{'#'} will be prepended to it.
        @type key: C{str}
        @param key: If specified, the key used to join the channel.
        """
        self.factory.state.Join(self, channel)

    def leave(self, channel, reason=None):
        """
        Leave a channel.

        @type channel: C{str}
        @param channel: The name of the channel to leave. If it has no prefix,
            C{'#'} will be prepended to it.
        @type reason: C{str}
        @param reason: If given, the reason for leaving.
        """
        self.factory.state.Part(self, channel, reason)

    part = leave

    def kick(self, channel, user, reason=None):
        """
        Attempt to kick a user from a channel.

        @type channel: C{str}
        @param channel: The name of the channel to kick the user from. If it has
            no prefix, C{'#'} will be prepended to it.
        @type user: C{str}
        @param user: The nick of the user to kick.
        @type reason: C{str}
        @param reason: If given, the reason for kicking the user.
        """

    def topic(self, channel, topic=None):
        """
        Attempt to set the topic of the given channel, or ask what it is.

        If topic is None, then I sent a topic query instead of trying to set the
        topic. The server should respond with a TOPIC message containing the
        current topic of the given channel.

        @type channel: C{str}
        @param channel: The name of the channel to change the topic on. If it
            has no prefix, C{'#'} will be prepended to it.
        @type topic: C{str}
        @param topic: If specified, what to set the topic to.
        """

    def mode(self, chan, set, modes, limit = None, user = None, mask = None):
        """
        Change the modes on a user or channel.

        The C{limit}, C{user}, and C{mask} parameters are mutually exclusive.

        @type chan: C{str}
        @param chan: The name of the channel to operate on.
        @type set: C{bool}
        @param set: True to give the user or channel permissions and False to
            remove them.
        @type modes: C{str}
        @param modes: The mode flags to set on the user or channel.
        @type limit: C{int}
        @param limit: In conjuction with the C{'l'} mode flag, limits the
             number of users on the channel.
        @type user: C{str}
        @param user: The user to change the mode on.
        @type mask: C{str}
        @param mask: In conjuction with the C{'b'} mode flag, sets a mask of
            users to be banned from the channel.
        """

    def msg(self, dest, message, length = None):
        """Send a message to a user or channel.

        @type dest: C{str}
        @param dest: The username or channel name to which to direct the
        message.

        @type message: C{str}
        @param message: The text to send

        @type length: C{int}
        @param length: The maximum number of octets to send at a time.  This
        has the effect of turning a single call to msg() into multiple
        commands to the server.  This is useful when long messages may be
        sent that would otherwise cause the server to kick us off or silently
        truncate the text we are sending.  If None is passed, the entire
        message is always send in one command.
        """

    say = msg

    def notice(self, user, message):
        """
        Send a notice to a user.

        Notices are like normal message, but should never get automated
        replies.

        @type user: C{str}
        @param user: The user to send a notice to.
        @type message: C{str}
        @param message: The contents of the notice to send.
        """

    def away(self, message=''):
        """
        Mark this client as away.

        @type message: C{str}
        @param message: If specified, the away message.
        """

    def back(self):
        """
        Clear the away status.
        """

    def whois(self, nickname, server=None):
        """
        Retrieve user information about the given nick name.

        @type nickname: C{str}
        @param nickname: The nick name about which to retrieve information.

        @since: 8.2
        """

    def register(self, nickname, hostname='foo', servername='bar'):
        """
        Login to the server.

        @type nickname: C{str}
        @param nickname: The nickname to register.
        @type hostname: C{str}
        @param hostname: If specified, the hostname to logon as.
        @type servername: C{str}
        @param servername: If specified, the servername to logon as.
        """

    def setNick(self, nickname):
        """
        Set this client's nickname.

        @type nickname: C{str}
        @param nickname: The nickname to change to.
        """

    def quit(self, message = ''):
        """
        Disconnect from the server

        @type message: C{str}

        @param message: If specified, the message to give when quitting the
            server.
        """

    ### user input commands, client->client

    def describe(self, channel, action):
        """
        Strike a pose.

        @type channel: C{str}
        @param channel: The name of the channel to have an action on. If it
            has no prefix, it is sent to the user of that name.
        @type action: C{str}
        @param action: The action to preform.
        @since: 9.0
        """

    def me(self, channel, action):
        """
        Strike a pose.

        This function is deprecated since Twisted 9.0. Use describe().

        @type channel: C{str}
        @param channel: The name of the channel to have an action on. If it
            has no prefix, C{'#'} will be prepended to it.
        @type action: C{str}
        @param action: The action to preform.
        """

    def ping(self, user, text = None):
        """
        Measure round-trip delay to another IRC client.
        """

    def badMessage(self, line, excType, excValue, tb):
        pass

    def quirkyMessage(self, s):
        pass

    ### Protocol methods

    def connectionMade(self):
        """
        Called once the we're connected
        """

    def dataReceived(self, data):
        """
        This is a fake protocol module
        """

    def lineReceived(self, line):
        """
        This is a fake protocol module
        """

    def getUserModeParams(self):
        """
        Get user modes that require parameters for correct parsing.

        @rtype: C{[str, str]}
        @return C{[add, remove]}
        """
        return ['', '']

    def getChannelModeParams(self):
        """
        Get channel modes that require parameters for correct parsing.

        @rtype: C{[str, str]}
        @return C{[add, remove]}
        """
        # PREFIX modes are treated as "type B" CHANMODES, they always take
        # parameter.
        params = ['', '']
        prefixes = self.supported.getFeature('PREFIX', {})
        params[0] = params[1] = ''.join(prefixes.iterkeys())

        chanmodes = self.supported.getFeature('CHANMODES')
        if chanmodes is not None:
            params[0] += chanmodes.get('addressModes', '')
            params[0] += chanmodes.get('param', '')
            params[1] = params[0]
            params[0] += chanmodes.get('setParam', '')
        return params

    def handleCommand(self, command, prefix, params):
        """ silently eat these """

    def __getstate__(self):
        dct = self.__dict__.copy()
        dct['dcc_sessions'] = None
        dct['_pings'] = None
        return dct

    def getModeParams(self, supported):
        """
        Get user modes that require parameters for correct parsing.

        @rtype: C{[str, str]}
        @return C{[add, remove]}
        """
        return ['', '']

    def modeChanged(self, source, dest, added, removed):
        """Called when users or channel's modes are changed.

        @type source: C{Client}
        @param source: The user and hostmask which instigated this change.

        @type dest: C{Client} or C{Channel}
        @param dest: The place where the modes are changed. If args is
        empty the channel for which the modes are changing.

        @type added: C{tuple of str}
        @param added: (modes, args)

        @type removed: C{tuple of str}
        @param removed: (modes, args)

        """

    def _modeChanged(self, source, dest, added, removed):
        if (dest == self):
            for at in added:
                if at[1]:
                    print "unhandled user mode argument %s for %s on %s" % (at[1], at[0], self)
                else:
                    if at[0] not in self.modes:
                        ml = list(self.modes)
                        ml.append(at[0])
                        ml.sort()
                        self.modes = ''.join(ml)
            for at in removed:
                if at[1]:
                    print "unhandled user mode argument for %s on %s" % (at[0], self)
                else:
                    if at[0] in self.modes:
                        ml = list(self.modes)
                        ml.remove(at[0])
                        self.modes = ''.join(ml)
        self.modeChanged(source, dest, added, removed)

    def ChgHost(self, newhost):
        self.host = newhost

    def _topicUpdated(self, client, channel, topic):
        pass

    def _userKicked(self, kickee, channel, kicker, message):
        pass

    def _userJoined(self, client, channel):
        pass

    def _userLeft(self, client, channel, message):
        pass

    def _userQuit(self, client, message):
        pass

    def kline(self, duration, usermask, hostmask, reason):
        self.factory.state.Kline(self, duration, usermask, hostmask, reason)

    def kill(self, killee, message):
        self.factory.state.Kill(self, killee, message)

class TS6Client(Client):
    def __init__(self, factory, server, nick, *args, **kwargs):
        defl = { 'user' : 'twisted',
                 'host' : server.name,
                 'hiddenhost' : '*',
                 'gecos' : 'twisted-ts6 client',
                 'modes' : '+',
                 'login' : None,
                 'ts' : int(time.time()),
                 }
        kwargs['defaults'] = defl
        Client.__init__(self, server, nick, *args, **kwargs)
        self.factory = factory
        self.uid = server.sid + self.factory.state.mkuid()

    def connectionMade(self):
        """
        Called once the we're connected
        """
        self.supported = self.factory.supports
        self.register(self.nick)

    def register(self, nickname, hostname='foo', servername='bar'):
        """
        Login to the server.

        @type nickname: C{str}
        @param nickname: The nickname to register.
        @type hostname: C{str}
        @param hostname: If specified, the hostname to logon as.
        @type servername: C{str}
        @param servername: If specified, the servername to logon as.
        """
        self.nick = nickname
        self.signedOn()

    def _privmsg(self, source, dest, message):
        if (len(message) > 0) and (message[0] == '\x01') and (message[-1] == '\x01'):
            m = ctcpExtract(message)
            if m['extended']:
                self.ctcpQuery(source, dest, m['extended'])
            if not m['normal']:
                return
            message = string.join(m['normal'], ' ')
        self.privmsg(source, dest, message)

    def msg(self, dest, message, length = None):
        """Send a message to a user or channel.

        @type dest: C{Client} or C{Channel}
        @param dest: The Client or Channel object to which to direct the
        message.

        @type message: C{str}
        @param message: The text to send

        @type length: C{int}
        @param length: The maximum number of octets to send at a time.  This
        has the effect of turning a single call to msg() into multiple
        commands to the server.  This is useful when long messages may be
        sent that would otherwise cause the server to kick us off or silently
        truncate the text we are sending.  If None is passed, the entire
        message is always send in one command.
        """
        self.factory.state.Privmsg(self, dest, message)

    def _noticed(self, source, dest, message):
        self.noticed(source, dest, message)

    def notice(self, dest, message, length=None):
        """
        Send a notice to a user or channel.

        Notices are like normal message, but should never get automated
        replies.

        @type user: C{Client} or C{Channel}
        @param user: The user to send a notice to.
        @type message: C{str}
        @param message: The contents of the notice to send.
        """
        self.factory.state.Notice(self, dest, message)

    def _userLeft(self, client, channel, message):
        self.userLeft(client, channel, message)

    def _userQuit(self, client, message):
        self.userQuit(client, message)

    def _userJoined(self, client, channel):
        self.userJoined(client, channel)

    def _userKicked(self, kickee, channel, kicker, message):
        self.userKicked(kickee, channel, kicker, message)

    def _userRenamed(self, oldnick, client):
        self.userRenamed(oldnick, client)

    def _topicUpdated(self, client, channel, topic):
        self.topicUpdated(client, channel, topic)

    def ctcpQuery(self, source, dest, messages):
        """
        Dispatch method for any CTCP queries received.
        """
        for m in messages:
            method = getattr(self, "ctcpQuery_%s" % m[0], None)
            if method:
                method(source, dest, m[1])
            else:
                self.ctcpUnknownQuery(source, dest, m[0], m[1])

    def ctcpUnknownQuery(self, source, dest, type, messages):
        pass

    def ctcpMakeReply(self, user, messages):
        self.notice(user, ctcpStringify(messages))

    def ctcpQuery_PING(self, user, channel, data):
        self.ctcpMakeReply(user, [("PING", data)])


class IRCClient(TS6Client):
    def __sendLine(self, line):
        self.conn.sendLine(line)

    def _reallySendLine(self, line):
        """ Should not be called directly
            - IRCClient function that assumes it's speaking to a real server
        """
        pass

    def sendLine(self, line):
        """ Should not be called directly
            - IRCClient function that assumes it's speaking to a real server
        """
        pass

    def _sendLine(self):
        """ Should not be called directly
            - IRCClient function that assumes it's speaking to a real server
        """
        pass

    def _privmsg(self, source, dest, message):
        if (len(message) > 0) and (message[0] == '\x01') and (message[-1] == '\x01'):
            m = ctcpExtract(message)
            if m['extended']:
                self.ctcpQuery(str(source), str(dest), m['extended'])
            if not m['normal']:
                return
            message = string.join(m['normal'], ' ')
        self.privmsg(str(source), str(dest), message)

    def msg(self, dest, message, length = None):
        """Send a message to a user or channel.

        @type dest: C{str}
        @param dest: The nick or channel to which to direct the
        message.

        @type message: C{str}
        @param message: The text to send

        @type length: C{int}
        @param length: The maximum number of octets to send at a time.  This
        has the effect of turning a single call to msg() into multiple
        commands to the server.  This is useful when long messages may be
        sent that would otherwise cause the server to kick us off or silently
        truncate the text we are sending.  If None is passed, the entire
        message is always send in one command.
        """
        if (dest[0] in self.supported.getFeature('CHANTYPES', {})):
            TS6Client.msg(self, self.factory.state.Channel(dest), message, length)
        else:
            TS6Client.msg(self, self.factory.state.ClientByNick(dest), message, length)

    def _noticed(self, source, dest, message):
        self.noticed(str(source), str(dest), message)

    def notice(self, dest, message, length=None):
        """
        Send a notice to a user or channel.

        Notices are like normal message, but should never get automated
        replies.

        @type user: C{str}
        @param user: The user or channel to send a notice to.
        @type message: C{str}
        @param message: The contents of the notice to send.
        """
        if (dest[0] in self.supported.getFeature('CHANTYPES', {})):
            TS6Client.notice(self, self.factory.state.Channel(dest), message, length)
        else:
            TS6Client.notice(self, self.factory.state.ClientByNick(dest), message, length)

    def _left(self, channel):
        self.left(str(channel))

    def left(self, channel):
        pass

    def _userLeft(self, client, channel, message):
        self.userLeft(str(client), str(channel), message)

    def _joined(self, channel):
        self.joined(channel)

    def _userJoined(self, client, channel):
        self.userJoined(str(client), str(channel))

    def _kickedFrom(self, channel, kicker, message):
        self.kickedFrom(str(channel), str(kicker), message)

    def _userKicked(self, kickee, channel, kicker, message):
        self.userKicked(str(kickee), str(channel), str(kicker), message)

    def _userRenamed(self, oldnick, client):
        visible = False
        for ch in self.factory.state.chansbyuid[self.uid]:
            if client in ch.clients:
                visible = True
        if visible:
            self.userRenamed(oldnick, client.nick)

    def _topicUpdated(self, client, channel, topic):
        self.topicUpdated(str(client), str(channel), topic)

    def ctcpQuery_PING(self, user, channel, data):
        nick = user.split("!")[0]
        self.ctcpMakeReply(nick, [("PING", data)])

    def modeChanged(self, user, channel, set, modes, args):
        """Called when users or channel's modes are changed.

        @type user: C{str}
        @param user: The user and hostmask which instigated this change.

        @type channel: C{str}
        @param channel: The channel where the modes are changed. If args is
        empty the channel for which the modes are changing. If the changes are
        at server level it could be equal to C{user}.

        @type set: C{bool} or C{int}
        @param set: True if the mode(s) is being added, False if it is being
        removed. If some modes are added and others removed at the same time
        this function will be called twice, the first time with all the added
        modes, the second with the removed ones. (To change this behaviour
        override the irc_MODE method)

        @type modes: C{str}
        @param modes: The mode or modes which are being changed.

        @type args: C{tuple}
        @param args: Any additional information required for the mode
        change.
        """

    def _modeChanged(self, source, dest, added, removed):
        if added:
            modes, params = zip(*added)
            self.modeChanged(str(source), str(dest), True, ''.join(modes), params)
        if removed:
            modes, params = zip(*removed)
            self.modeChanged(str(source), str(dest), False, ''.join(modes), params)
