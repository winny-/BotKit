class Color:
    def __init__(self):
        pass

    Black = "01"
    White = "00"
    Gray = "14"
    LGray = "15"
    Blue = "02"
    Cyan = "10"
    Green = "03"
    Magenta = "06"
    Red = "04"
    Yellow = "08"
    LBlue = "12"
    LCyan = "11"
    LGreen = "09"
    LMagenta = "13"
    LBrown = "05"
    Orange = "07"


def SetColor(s, color):
    return "\x03%s%s\x0f" % (color, s)


def Bold(s):
    return "\x02%s\x0f" % s


def Invert(s):
    return "\x16%s\x0f" % s


def Underline(s):
    return "\x15%s\x0f" % s


def Trunicate(s, l=30, append="..."):
    return s[:l].rsplit(' ', 1)[0]+append if len(s) > l else s
