import sys


def shall_mock():
    import sys
    if 'esp' not in sys.platform and sys.implementation.name is not 'micropython':
        init_mocks()
        return True
    return False


def init_mocks():
    if 'esp' not in sys.platform and sys.implementation.name is not 'micropython':
        import time
        import re
        import errno
        import select
        import socket
        import asyncio
        import io
        import json
        import collections
        from unittest.mock import Mock
        sys.modules['utime'] = time
        sys.modules['micropython'] = Mock()
        sys.modules['dht'] = Mock()
        sys.modules['ure'] = re
        sys.modules['uerrno'] = errno
        sys.modules['uselect'] = select
        sys.modules['usocket'] = socket
        sys.modules['uasyncio'] = asyncio
        sys.modules['uio'] = io
        sys.modules['machine'] = Mock()
        sys.modules['ucollections'] = Mock()
        sys.modules['ujson'] = json
        sys.modules['network'] = Mock()
        sys.modules['webrepl'] = Mock()
        sys.modules['umqtt.simple2'] = Mock()
        sys.modules['ticks_add'] = Mock()
        sys.modules['ucollections'] = collections
        time.ticks_add = Mock()
        time.ticks_ms = Mock()
        time.ticks_diff = Mock()
        time.sleep_ms = lambda x: time.sleep(x / 1000)
        asyncio.sleep_ms = lambda x: asyncio.sleep(x / 1000)
        sys.print_exception = lambda *x: print(x)
    if sys.platform is not 'esp' and sys.implementation.name is 'micropython':
        pass


DEFAULT_PIN_VALUE = {12: 0, 13: 0, 14: 1}

class Pin:
    PULL_UP = 0
    IN = 0
    OUT = 0

    def __init__(self, *args, **kwargs):
        self.pin = args[0]

    def value(self, *args):
        v = DEFAULT_PIN_VALUE.get(self.pin, 0)
        print('pin', self.pin, 'return', v)
        return v


class DHT22:
    def __init__(self, *args):
        pass

    def measure(self):
        pass

    def temperature(self):
        return 22.3

    def humidity(self):
        return 99

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

def settime():
    pass

class Timer:
    PERIODIC = 0
    def init(self, *args, **kwargs):
        pass