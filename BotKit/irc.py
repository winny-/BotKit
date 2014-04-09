#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import ssl
import socket
import thread
import traceback
import urllib2
from .log import ColoredLogger
from .structs import *
from .decorators import getcallback, getcommand
from .admin import admin
from .ignore import ignore

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
            self.logger.info("Socket opened using ssl")
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
                    self._buffer.append(response)
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
                self._buffer.pop()
                
            self.msg('NICKSERV', 'IDENTIFY %s' % self._nickpass)
            while True:
                response = self.receive()
                self._buffer.append(response)
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
            self._buffer.pop()

        if len(self._channels) > 0:
            self.join(self._channels)

        #main loop
        while self.running:
            line = self._buffer.pop(0) if len(self._buffer) > 0 else self.receive()
            if len(line.prefix.split('!')) == 2 and ignore().isignored(line.prefix.split('!')[0]):
                continue

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
                    self.logger.info("Got CTCP request from %s: %s" % (user, cmd))
                    self._callback('ctcp_'+cmd, channel, user, args)
                else:
                    self._callback('msg', channel, user, line.trailing)
                    if line.trailing[0] == self._prefix and len(line.trailing) > 1:
                        cmd = line.trailing[1:].split()[0]
                        self._command(cmd, channel, user, line.trailing[2+len(cmd):])
            elif line.command == 'INVITE':
                self._callback('invite', line.trailing, line.prefix.split('!')[0])

    ######
    # Private methods
    ######
    def _invoke(self, method, *args):
        if self._blocking is True:
            self._invokehandler(method, *args)
        else:
            thread.start_new(self._invokehandler, (method,) + args)
    
    def _invokehandler(self, method, *args):                                    
        try:                                                                    
            method(*args)                                                       
        except Exception, e:                                                    
            self.logger.error("Exception occured during invoke: %s" % e)        
            if self._debug is True:                                             
                print traceback.format_exc()                                    
            if self._debug:                                                     
                self.msg(args[1], "Something went wrong: " + urllib2.urlopen("https://nnmm.nl/", "%s\n\n%s" % (e ,traceback.format_exc())).read())
            else:                                                               
                self.msg(args[1], "Something went wrong") 

    def _callback(self, ctype, *args):
        for c in getcallback(ctype):
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

    def action
