#!/usr/bin/python

import botlib, random, re, sys
from cowsay import cowsay
from bs4 import BeautifulSoup
from urllib import urlopen

class callback(botlib.callback):
	def msg(self, bot, user, channel, msg):
		print user+" in "+channel+": "+msg		

	def action(self, bot, user, channel, action):
		print user+" in "+channel+" did "+action

	def join(self, bot, user, channel):
		print user+" joined "+channel
		bot.msg(channel, random.choice(['Hey','What\'s up','Yo','What\'s new'])+' '+user)

class commands(botlib.commands):
	def help(self, bot, user, channel, args):
		bot.msg(channel,"The is a help message")

	def randint(self, bot, user, channel, args):
		a = self._parseArgs(args)
		a.sort()
		if(len(a) != 2):
			bot.msg(channel, "I need 2 arguments for that command")
		elif(not str(a[0]).replace('-','').isdigit() or not str(a[1]).replace('-','').isdigit()):
			bot.msg(channel, "Both arguments need to be numeric")
		else:
			try: bot.msg(channel, random.randint(a[0],a[1]))
			except Exception, e: bot.msg(channel, str(e))

	def quit(self, bot, user, channel, args):
		if(args == ""): bot.quit()
		else: bot.quit(args)


irc = botlib.con('irc.freenode.net', 6667, ['#superbossgames'], 'Dumbo', callback(), commands())
irc.go()

