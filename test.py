#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Just to check if there are any syntax errors etc

from BotKit import *

irc = BotKit(
    nickname="botkit_test",
    channels="#/g/spam",
    host="irc.rizon.net",
    port=9999,
    ssl=True
)


@handles('msg')
def parse(bot, channel, user, msg):
    pass  # dummy


@command('test')
def parse(bot, channel, user, msg):
    pass  # dummy


@command('addadmin', True)
def parse(bot, channel, user, args):
    usr = args.split()[0]
    if admin().isadmin(usr):
        bot.msg(channel, "%s: %s is already an admin" % (user, usr))
    else:
        admin().addadmin(usr)
        bot.msg(channel, "%s: I added %s to the admin group" % (user, usr))


@command('admins')
def parse(bot, channel, user, args):
    bot.msg(channel, "%s: %s" % (user, ', '.join(admin().getadmins())))


@command('remadmin', True)
def parse(bot, channel, user, args):
    usr = args.split()[0]
    if usr.lower() == user.lower():
        bot.msg(channel, 'lol okay')

    if admin().isadmin(usr):
        admin().removeadmin(usr)
        bot.msg(channel, "%s: I removed %s from the admin group" % (user, usr))
    else:
        bot.msg(channel, "%s: %s was never an admin" % (user, usr))


@command('blah', True)
def blah(bot, channel, user, args):
    bot.msg(channel, "%s: BLAH!" % user)


@command('ignore', True)
def ign(bot, channel, user, args):
    ignore().add(args.split()[0])
    bot.msg(channel, "Now ignoring %s" % args.split()[0])


#irc.run()
