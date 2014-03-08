_commands = []
_callbacks = []


def command(name, restricted=False):
    """
    Decorator to add a command

    @type name: str
    @param name: The command name. This is how the command will be called
    @type restricted: bool
    @param restricted: if this is an admin-only command
    @return: decorator
    """
    global _commands
    def decorator(f):
        _commands.append({
            "command": name.lower(),
            "method": f,
            "restricted": restricted
        })
    return decorator

def handles(ctype, raw=False):
    """
    Supported types (non-raw):
        cctp_*; (bot, user, arguments),
        msg; (bot, channel, user, msg),
        notice; (bot, target, user, notice),
        invite; (bot, channel, user),
        nick; (bot, user, nick),
        quit; (bot, user, reason),
        part; (bot, channel, user, reason),
        join; (bot, channel, user)
        kick; (bot, channel, user, target, reason)
        mode; (bot, channel, user, target, mode)

    @type ctype: str
    @param ctype: The irc command type.
    @type raw: bool
    @param raw: If set to True the decorator will do a callback for the parsed line. Callback type: parse(bot, message)
    @return: decorator
    """
    global _callbacks

    def decorator(f):
        _callbacks.append({
            "type": ctype,
            "method": f,
            "raw": raw
        })
    return decorator


def getcommand(name):
    """
    returns the requested command method

    @type name: str
    @param name:
    @return: method
    @rtype: dict
    """
    global _commands
    return [c for c in _commands if c['command'] == name.lower()]


def getcallback(name, raw=False):
    """
    returns the requested callback

    @type name: str
    @param name:
    @type raw: bool
    @param raw:
    @return: method
    @rtype: list
    """
    global _callbacks
    return [c['method'] for c in _callbacks if c['type'] == name.lower() and c['raw'] == raw]
