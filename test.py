#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Just to check if there are any syntax errors etc

from BotKit import *

irc = BotKit(
    nickname="travis_botkit",
    channels="#/g/spam",
    host="irc.rizon.net",
    port=9999,
    ssl=True
)

@handles('msg')
def parse(bot, channel, user, msg):
    pass #dummy

@command('test')
def parse(bot, channel, user, msg):
    pass #dummy