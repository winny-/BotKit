#!/usr/bin/python
import botlib

class callback(botlib.callback):
	def quit(self, bot, user, channel, message):
		print user+" quit("+message+")"

	def msg(self, bot, user, channel, msg):
		print user+" in "+channel+": "+msg		

	def action(self, bot, user, channel, action):
		print user+" in "+channel+" did "+action

class commands(botlib.commands):
	def eat(self, bot, user, channel, args):
		bot.action(channel, 'eats a carrot')
		bot.msg(channel, 'Eh, what\'s up doc?')

	def helloworld(self, bot, user, channel, args):
		bot.msg(channel, "Hello World!")


irc = botlib.connection('irc.freenode.net', 6667, ['#secrettest'], 'testbot9000', callback(), commands())
irc.go()

