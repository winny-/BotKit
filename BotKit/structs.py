#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Struct-ish stuff

class Message(object):
    """
    Parsed message object
    """
    def __init__(self, line):
        line = line.split(' :', 1)
        split = line[0].split(' ', 2)
        self.prefix = split[0]
        self.command = split[1]
        self.arguments = split[2] if len(split) >= 3 else False
        self.trailing = line[1] if len(line) == 2 else False


class User(object):
    """
    A parsed user
    """
    def __init__(self, nick, host, user, mode, realname):
        """
        @type nick: str
        @type host: str
        @type user: str
        @type mode: str
        @type channels: list

        @param nick: Nickname
        @param host: Hostmask
        @param user: Username
        @param mode: Usermodes
        @param realname: Real name
        """

        self.nick = nick
        self.host = host
        self.user = user
        self.mode = mode
        self.realname = realname
