#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import ssl
import socket
import thread
import traceback
from .log import ColoredLogger
from .structs import *
from .decorators import getcallback, getcommand
from .admin import admin

class BotKit(object):
    def __init__(self, **kwargs):
        """
        @param host: The server ip/host (default '127.0.0.1')
        @param port: The server port (default 6667)
        @param ssl: Should ssl be used (default False)
        @param nickname: Bot nickname (default 'testbot')
        @param nickpass: Bot password to authenticate with the nickserv with (default False)
        @param user: Bot user (default 'bot')
        @param realname: Bot realname (default 'bot')
        @param channels: Autoconnect channels (default [])
        @param logfile: desired logfile or False
        @param verbose: Verbose output (default False)
        @param debug: Debug output (default False)
        @param prefix: Command prefix (default ':')
        @param blocking: Use blocking callbacks (default False)

        @type host: str
        @type port: int
        @type ssl: bool
        @type nickname: str
        @type nickpass: str
        @type user: str
        @type realname: str
        @type channels: list
        @type logfile: str
        @type verbose: bool
        @type debug: bool
        @type prefix: str
        @type blocking: bool
        """
        self._buffer = []
        self.running = False
        self._sock = None
        self.logger = ColoredLogger('BotKit', kwargs.get('logfile', False) or False)

        # Connection properties
        self._host = kwargs.get('host', '127.0.0.1')
        self._port = int(kwargs.get('port', 6667))
        self._ssl = kwargs.get('ssl', False)

        self._nickname = kwargs.get('nickname', 'testbot')
        self._nickpass = kwargs.get('nickpass', False) or False
        self._user = kwargs.get('user', 'bot')
        self._realname = kwargs.get('realname', 'bot')

        self._channels = kwargs.get('channels', [])
        if type(self._channels) == str:
            self._channels = self._channels.split(',')
        self._verbose = kwargs.get('verbose', False)
        self._debug = kwargs.get('debug', False)
        self._prefix = kwargs.get('prefix', ':')
        self._blocking = kwargs.get('blocking', False)
        self._serverinfo = {}
        self._more = ""

    def run(self):
        """
        Starts the bot

        @return: None
        """
        #create the connection
        self.logger.info("Connecting to %s:%i" % (self._host, self._port))
        if self._ssl:
            irc_unencrypted = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock = ssl.wrap_socket(irc_unencrypted)
            self._sock.connect((self._host, self._port))
            self.logger.info("Using ssl")
        else:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.connect((self._host, self._port))

        self.user(self._user, self._realname)
        self.nick(self._nickname)

        preferednick = self._nickname
        while True:
            response = self.receive()
            if response.command == '001':
                break
            elif response.command == '433':
                self.nick(self._nickname + "_")
        self.logger.info("Connected: %s" % response.trailing)
        self.running = True
        
        if self._nickpass is not False:
            if preferednick != self._nickname:
                self.msg('NICKSERV', 'GHOST %s %s' % (preferednick, self._nickpass))
                while True:
                    response = self.receive()
                    if response.command != "NOTICE":
                        continue
                    if 'has been ghosted' in response.trailing:
                        self.nick(preferednick)
                        self.logger.info("Ghosted %s" % preferednick)
                        break
                    elif 'invalid password for' in response.trailing:
                        self.logger.warning("Could not ghost %s: %s" % (preferednick, response.trailing))
                        self._nickpass = False
                        break
                    elif "Your nick isn't registered" in response.trailing:
                        self.logger.warning('Tried authing but the nickname is not registered')
                        self._nickpass = False

            self.msg('NICKSERV', 'IDENTIFY %s' % self._nickpass)
            while True:
                response = self.receive()
                if response.command != "NOTICE":
                    continue
                if 'accepted' in response.trailing or 'identified' in response.trailing:
                    self.logger.info(response.trailing)
                    break
                elif "Your nick isn't registered" in response.trailing:
                    self.logger.warning('Tried authing but the nickname is not registered')
                    self._nickpass = False
                    break
                elif "invalid password" in response.trailing:
                    self.logger.warning('Could not authenticate: %s' % response.trailing)
                    break

        if len(self._channels) > 0:
            self.join(self._channels)

        #main loop
        while self.running:
            line = self._buffer.pop(0) if self._buffer == 0 else self.receive()
            for c in getcallback(line.command, True):
                self._callback(c, line)

            if line.command == "PRIVMSG":
                user = line.prefix.split('!')[0]
                channel = line.arguments
                if channel == self._nickname:
                    channel = user
                if line.trailing[-1] == "\001" and line.trailing[0] == "\001":
                    cmd = line.trailing[1:-1].split()[0].lower()
                    args = line.trailing[2+len(cmd):-1]
                    self._callback('cctp_'+cmd, user, args)
                else:
                    self._callback('msg', channel, user, line.trailing)
                    if line.trailing[0] == self._prefix:
                        cmd = line.trailing[1:].split()[0]
                        self._command(cmd, channel, user, line.trailing[2+len(cmd):])
            elif line.command == 'INVITE':
                arg = line.arguments.split()
                self._callback('invite', line.trailing, line.prefix.split('!')[0])


    ######
    # Private methods
    ######
    def _invoke(self, method, *args):
        try:
            if self._blocking is True:
                method(*args)
            else:
                thread.start_new(method, args)
        except Exception, e:
            self.logger.error("Exception occured during invoke: %s" % e)
            if self._debug is True:
                print e
                print traceback.format_exc()

    def _callback(self, type, *args):
        for c in getcallback(type):
            self._invoke(c, self, *args)

    def _command(self, cmd, *args):
        adm = admin()
        for c in getcommand(cmd):
            if c['restricted'] and not adm.isadmin(args[1]):
                self.msg(args[0], "I'm sorry %s. I can't let you do that" % args[1])
                self.logger.info("%s tried to use the command %s but is not an admin" % (args[1], cmd))
            elif c['restricted'] and adm.isadmin(args[1]) and not 'r' in self.who(args[1]).mode:
                self.msg(args[0], "%s: You must be authenticated to do that" % args[1])
                self.logger.info("%s tried to use the command %s but is not authenticated" % (args[1], cmd))
            else:
                self._invoke(c['method'], self, *args)

    def _lsend(self, s):
        if self._verbose:
            print s
        self._sock.send(s + '\r\n')

    def _lrecv(self):
        c, s = '', ''
        while c != '\n':
            c = self._sock.recv(1)
            if c == '':
                break
            s += c
        line = s.strip('\r\n')
        if self._verbose:
            print line

        if line.split(':')[0] == "PING ":
            self._lsend('PONG :%s' % line.split(':')[1])
            return self._lrecv()
        return line

    def receive(self):
        """
        Receive one line

        @rtype: Message
        @return: Message object
        """
        line = self._lrecv()[1:]
        return Message(line)


    ######
    # Bot info
    ######
    def getnick(self):
        """
        Gets the current nickname

        @rtype: str
        @return: Current nickname
        """
        return self._nickname

    ######
    # Server commands
    ######
    def user(self, user, realname):
        """
        Sends user info to the server

        @type user: str
        @type realname: str
        @param user: username
        @param realname: Real name
        """
        self._lsend("USER %s 0 0 :%s" % (user, realname))

    def msg(self, what, msg):
        """
        Sends an irc message

        @type what: str
        @type msg: str
        @param what: Destination
        @param msg: Message text
        """
        for line in str(msg).replace('\r', '').split('\n'):
            self._lsend('PRIVMSG %s :%s' % (what, line))

    def action(self, what, msg):
        """
        Sends an irc action

        @type what: str
        @type msg: str
        @param what: Destination
        @param msg: Action text
        """
        self._lsend('PRIVMSG %s :\001ACTION %s\001' % (what, str(msg)))

    def join(self, channel):
        """
        Make the bot join a channel or multiple channels

        @type channel: str
        @type channel: list
        @param channel: Channel(s) to join
        """
        if type(channel) == list:
            channel = ','.join(channel)
        channel = channel.split()[0].replace('\n', '')
        self.logger.info("Joining " + channel)
        self._lsend('JOIN ' + channel)

    def part(self, channel, reason=" "):
        """
        Makes the bot leave(part) a channel

        @type channel: str
        @type reason: str
        @param channel: The channel that will be left
        @param reason: Reason for leaving
        """
        self.logger.info("Parting from channel %s: %s"% (channel, str(reason.replace('\n', ''))))
        self._lsend('PART %s :%s' % (channel, str(reason.replace('\n', ''))))

    def quit(self, reason="Bot shutting down"):
        """
        Disconnect from the irc server

        @param reason: Quit reason
        """
        self.logger.info("Shutting down: " + reason)
        self._lsend('QUIT :' + str(reason.replace('\n', '')))
        self.running = False

    def nick(self, nick):
        """
        Set the new nickname for the bot

        @type nick: str
        @param nick: Nickname
        """
        self._lsend('NICK %s 0' % nick.replace('\n', ''))
        self._nickname = nick.replace('\n', '')

    def names(self, channel):
        """
        Returns a list of users in the specified channel

        @todo: Redo the entire function
        @param channel: target
        @return: list of users
        @rtype: list
        """
        self._lsend('NAMES ' + channel.replace('\n', ''))
        return self._lrecv().split(':')[2].split()

    def notice(self, target, message):
        """
        @type target: str
        @type message: str
        @param target: Target
        @param message: Notice message
        """
        self._lsend('NOTICE %s :%s' % (target, message))

    def who(self, who):
        """
        Returns a user object with info about the user

        @type who: str
        @param who: User
        @return: User object
        @rtype: User
        """
        self._lsend('WHO %s' % (who.split()[0]))
        resp = ""
        while not "352" in resp:
            resp = self._lrecv()
            self._buffer.append(Message(resp[1:]))
        self._buffer.pop()
        match = re.match(':\S+ \d+ \S+ \S+ ~(\S+) (\S+) \* (\S+) (\S+) :\d+ (\S+)', resp)
        return User(
            match.group(3),
            match.group(2),
            match.group(1),
            match.group(4),
            match.group(5)
        )

    def list(self):
        """
        @todo: Redo function, implement buffer
        @return: List of channels
        """
        self._lsend('LIST')
        channels = []
        while 1:
            raw = self._lrecv()
            if raw[-13:] == ":End of /LIST":
                break
            raw = raw.replace('\r', '').split('\n')
            for line in raw:
                try:
                    channels.append({"name": line.split(' ')[3],
                                     "users": int(line.split(' ')[4]),
                                     "desc": line.split(':')[2]})
                except:
                    pass
        return channels

    #####
    # usefull and TODO remove
    #####
    def SetMore(self, text):
        """
        @todo migrate
        @param text:
        """
        self._more = text

    def GetMore(self):
        """
        @todo: migrate
        @return: stored more text
        @rtype: str
        """
        ret = self._more
        self._more = ""
        return ret
