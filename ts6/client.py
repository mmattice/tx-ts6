#!/usr/bin/env python

import time

from ts6.channel import Channel

class _CommandDispatcherMixin(object):
    """
    Dispatch commands to handlers based on their name.

    Command handler names should be of the form C{prefix_commandName},
    where C{prefix} is the value specified by L{prefix}, and must
    accept the parameters as given to L{dispatch}.

    Attempting to mix this in more than once for a single class will cause
    strange behaviour, due to L{prefix} being overwritten.

    @type prefix: C{str}
    @ivar prefix: Command handler prefix, used to locate handler attributes
    """
    prefix = None

    def dispatch(self, commandName, *args):
        """
        Perform actual command dispatch.
        """
        def _getMethodName(command):
            return '%s_%s' % (self.prefix, command)

        def _getMethod(name):
            return getattr(self, _getMethodName(name), None)

        method = _getMethod(commandName)
        if method is not None:
            return method(*args)

        method = _getMethod('unknown')
        if method is None:
            raise UnhandledCommand("No handler for %r could be found" % (_getMethodName(commandName),))
        return method(commandName, *args)


class ServerSupportedFeatures(_CommandDispatcherMixin):
    """
    Handle ISUPPORT messages.

    Feature names match those in the ISUPPORT RFC draft identically.

    Information regarding the specifics of ISUPPORT was gleaned from
    <http://www.irc.org/tech_docs/draft-brocklesby-irc-isupport-03.txt>.
    """
    prefix = 'isupport'

    """
    ircd-seven-1.0.1(20100130-d3139a423e1f, Charybdis 3.2-dev). ballard.freenode.net eHIKMpSZ6 TS6ow 01H
        CHANTYPES=# EXCEPTS INVEX CHANMODES=eIbq,k,flj,CFLMPQScgimnprstz
        CHANLIMIT=#:120 PREFIX=(ov)@+ MAXLIST=bqeI:100 MODES=4
        NETWORK=freenode KNOCK STATUSMSG=@+ CALLERID=g SAFELIST ELIST=U
        CASEMAPPING=rfc1459 CHARSET=ascii NICKLEN=16 CHANNELLEN=50
        TOPICLEN=390 ETRACE CPRIVMSG CNOTICE DEAF=D MONITOR=100 FNC
        TARGMAX=NAMES:1,LIST:1,KICK:1,WHOIS:1,PRIVMSG:4,NOTICE:4,ACCEPT:,MONITOR:
        EXTBAN=$,arx WHOX CLIENTVER=3.0
    """

    def __init__(self):
        self._features = {
            'CHANNELLEN': 50,
            'CHANTYPES': tuple('#'),
            'MODES': 4,
            'NICKLEN': 16,
            'PREFIX': self._parsePrefixParam('(ov)@+'),
            # The ISUPPORT draft explicitly says that there is no default for
            # CHANMODES, but we're defaulting it here to handle the case where
            # the IRC server doesn't send us any ISUPPORT information, since
            # IRCClient.getChannelModeParams relies on this value.
            'CHANMODES': self._parseChanModesParam(['eIbq','k','flj','CFLMPQScgimnprstz'])}


    def _splitParamArgs(cls, params, valueProcessor=None):
        """
        Split ISUPPORT parameter arguments.

        Values can optionally be processed by C{valueProcessor}.

        For example::

            >>> ServerSupportedFeatures._splitParamArgs(['A:1', 'B:2'])
            (('A', '1'), ('B', '2'))

        @type params: C{iterable} of C{str}

        @type valueProcessor: C{callable} taking {str}
        @param valueProcessor: Callable to process argument values, or C{None}
            to perform no processing

        @rtype: C{list} of C{(str, object)}
        @return: Sequence of C{(name, processedValue)}
        """
        if valueProcessor is None:
            valueProcessor = lambda x: x

        def _parse():
            for param in params:
                if ':' not in param:
                    param += ':'
                a, b = param.split(':', 1)
                yield a, valueProcessor(b)
        return list(_parse())
    _splitParamArgs = classmethod(_splitParamArgs)


    def _unescapeParamValue(cls, value):
        """
        Unescape an ISUPPORT parameter.

        The only form of supported escape is C{\\xHH}, where HH must be a valid
        2-digit hexadecimal number.

        @rtype: C{str}
        """
        def _unescape():
            parts = value.split('\\x')
            # The first part can never be preceeded by the escape.
            yield parts.pop(0)
            for s in parts:
                octet, rest = s[:2], s[2:]
                try:
                    octet = int(octet, 16)
                except ValueError:
                    raise ValueError('Invalid hex octet: %r' % (octet,))
                yield chr(octet) + rest

        if '\\x' not in value:
            return value
        return ''.join(_unescape())
    _unescapeParamValue = classmethod(_unescapeParamValue)


    def _splitParam(cls, param):
        """
        Split an ISUPPORT parameter.

        @type param: C{str}

        @rtype: C{(str, list)}
        @return C{(key, arguments)}
        """
        if '=' not in param:
            param += '='
        key, value = param.split('=', 1)
        return key, map(cls._unescapeParamValue, value.split(','))
    _splitParam = classmethod(_splitParam)


    def _parsePrefixParam(cls, prefix):
        """
        Parse the ISUPPORT "PREFIX" parameter.

        The order in which the parameter arguments appear is significant, the
        earlier a mode appears the more privileges it gives.

        @rtype: C{dict} mapping C{str} to C{(str, int)}
        @return: A dictionary mapping a mode character to a two-tuple of
            C({symbol, priority)}, the lower a priority (the lowest being
            C{0}) the more privileges it gives
        """
        if not prefix:
            return None
        if prefix[0] != '(' and ')' not in prefix:
            raise ValueError('Malformed PREFIX parameter')
        modes, symbols = prefix.split(')', 1)
        symbols = zip(symbols, xrange(len(symbols)))
        modes = modes[1:]
        return dict(zip(modes, symbols))
    _parsePrefixParam = classmethod(_parsePrefixParam)


    def _parseChanModesParam(self, params):
        """
        Parse the ISUPPORT "CHANMODES" parameter.

        See L{isupport_CHANMODES} for a detailed explanation of this parameter.
        """
        names = ('addressModes', 'param', 'setParam', 'noParam')
        if len(params) > len(names):
            raise ValueError(
                'Expecting a maximum of %d channel mode parameters, got %d' % (
                    len(names), len(params)))
        items = map(lambda key, value: (key, value or ''), names, params)
        return dict(items)
    _parseChanModesParam = classmethod(_parseChanModesParam)


    def getFeature(self, feature, default=None):
        """
        Get a server supported feature's value.

        A feature with the value C{None} is equivalent to the feature being
        unsupported.

        @type feature: C{str}
        @param feature: Feature name

        @type default: C{object}
        @param default: The value to default to, assuming that C{feature}
            is not supported

        @return: Feature value
        """
        return self._features.get(feature, default)


    def hasFeature(self, feature):
        """
        Determine whether a feature is supported or not.

        @rtype: C{bool}
        """
        return self.getFeature(feature) is not None


    def parse(self, params):
        """
        Parse ISUPPORT parameters.

        If an unknown parameter is encountered, it is simply added to the
        dictionary, keyed by its name, as a tuple of the parameters provided.

        @type params: C{iterable} of C{str}
        @param params: Iterable of ISUPPORT parameters to parse
        """
        for param in params:
            key, value = self._splitParam(param)
            if key.startswith('-'):
                self._features.pop(key[1:], None)
            else:
                self._features[key] = self.dispatch(key, value)


    def isupport_unknown(self, command, params):
        """
        Unknown ISUPPORT parameter.
        """
        return tuple(params)


    def isupport_CHANLIMIT(self, params):
        """
        The maximum number of each channel type a user may join.
        """
        return self._splitParamArgs(params, _intOrDefault)


    def isupport_CHANMODES(self, params):
        """
        Available channel modes.

        There are 4 categories of channel mode::

            addressModes - Modes that add or remove an address to or from a
            list, these modes always take a parameter.

            param - Modes that change a setting on a channel, these modes
            always take a parameter.

            setParam - Modes that change a setting on a channel, these modes
            only take a parameter when being set.

            noParam - Modes that change a setting on a channel, these modes
            never take a parameter.
        """
        try:
            return self._parseChanModesParam(params)
        except ValueError:
            return self.getFeature('CHANMODES')


    def isupport_CHANNELLEN(self, params):
        """
        Maximum length of a channel name a client may create.
        """
        return _intOrDefault(params[0], self.getFeature('CHANNELLEN'))


    def isupport_CHANTYPES(self, params):
        """
        Valid channel prefixes.
        """
        return tuple(params[0])


    def isupport_EXCEPTS(self, params):
        """
        Mode character for "ban exceptions".

        The presence of this parameter indicates that the server supports
        this functionality.
        """
        return params[0] or 'e'


    def isupport_IDCHAN(self, params):
        """
        Safe channel identifiers.

        The presence of this parameter indicates that the server supports
        this functionality.
        """
        return self._splitParamArgs(params)


    def isupport_INVEX(self, params):
        """
        Mode character for "invite exceptions".

        The presence of this parameter indicates that the server supports
        this functionality.
        """
        return params[0] or 'I'


    def isupport_KICKLEN(self, params):
        """
        Maximum length of a kick message a client may provide.
        """
        return _intOrDefault(params[0])


    def isupport_MAXLIST(self, params):
        """
        Maximum number of "list modes" a client may set on a channel at once.

        List modes are identified by the "addressModes" key in CHANMODES.
        """
        return self._splitParamArgs(params, _intOrDefault)


    def isupport_MODES(self, params):
        """
        Maximum number of modes accepting parameters that may be sent, by a
        client, in a single MODE command.
        """
        return _intOrDefault(params[0])


    def isupport_NETWORK(self, params):
        """
        IRC network name.
        """
        return params[0]


    def isupport_NICKLEN(self, params):
        """
        Maximum length of a nickname the client may use.
        """
        return _intOrDefault(params[0], self.getFeature('NICKLEN'))


    def isupport_PREFIX(self, params):
        """
        Mapping of channel modes that clients may have to status flags.
        """
        try:
            return self._parsePrefixParam(params[0])
        except ValueError:
            return self.getFeature('PREFIX')


    def isupport_SAFELIST(self, params):
        """
        Flag indicating that a client may request a LIST without being
        disconnected due to the large amount of data generated.
        """
        return True


    def isupport_STATUSMSG(self, params):
        """
        The server supports sending messages to only to clients on a channel
        with a specific status.
        """
        return params[0]


    def isupport_TARGMAX(self, params):
        """
        Maximum number of targets allowable for commands that accept multiple
        targets.
        """
        return dict(self._splitParamArgs(params, _intOrDefault))


    def isupport_TOPICLEN(self, params):
        """
        Maximum length of a topic that may be set.
        """
        return _intOrDefault(params[0])



class Client:
    def __init__(self, factory, server, nick, *args, **kwargs):
        self.factory = factory
        self.conn = None
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
            self.uid = server.sid + self.factory.state.mkuid()
        print "registered Client %s" % self

    def __str__(self):
        return '%s!%s@%s' % (self.nick, self.user, self.host)

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

    def modeset(self, modes):
        # XXX ignores user modes
        pass

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
        self.factory.state.Privmsg(self, dest, message)

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
        self.factory.state.Notice(self, user, message)

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
        self.nick = nickname
        self.signedOn()

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
        self.supported = ServerSupportedFeatures()
        self.register(self.nick)

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
