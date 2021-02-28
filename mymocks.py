class Pin:
    PULL_UP = 0
    IN = 0
    OUT = 0

    def __init__(self, *args, **kwargs):
        pass

    def value(self, *args):
        return 0

class network:
    class WLAN:
        def active(self, *args):
            pass
        def isconnected(self, *args):
            return True
        def ifconfig(self, *args):
            pass
    STA_IF = 0
    AP_IF = 1

def reset():
    pass

def webrepl():
    pass

class Timer:
    PERIODIC = 0
    def init(self, *args, **kwargs):
        pass