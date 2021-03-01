import sys


def init_mocks():
    if 'esp' not in sys.platform and sys.implementation.name is not 'micropython':
        mocked_python = None
        import time
        import re
        import errno
        import select
        import socket
        import asyncio
        import io
        import json
        from unittest.mock import Mock
        sys.modules['utime'] = time
        sys.modules['micropython'] = Mock()
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
        time.ticks_add = Mock()
        time.ticks_ms = Mock()
        time.ticks_diff = Mock()
        time.sleep_ms = lambda x: time.sleep(x / 1000)
        asyncio.sleep_ms = lambda x: asyncio.sleep(x / 1000)
        sys.print_exception = lambda *x: print(x)
    if sys.platform is not 'esp' and sys.implementation.name is 'micropython':
        darwin_micropython = None


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