# -*- coding: utf-8 -*-

__version__ = "2.0-dev"

from .irc import BotKit
from .log import ColoredLogger
from .decorators import command, handles
from .util import stylize, humanize
from .admin import admin
from .ignore import ignore