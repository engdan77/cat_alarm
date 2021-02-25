"""cat alarm: project for scaring cats"""

__license__ = "MIT"
__version__ = "0.0.1"
__email__ = "daniel@engvalls.eu"

import sys
if 'esp' not in sys.platform:
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



import gc
import mylogging
import mypicoweb
import uasyncio as asyncio
from mypinin import MyPinIn, blocking_count_clicks
from myconfig import get_config, save_config
from mywatchdog import WDT
from myled import blink_int
from mywifi import stop_all_wifi, start_ap, wifi_connect
from webresources import web_save, web_status, web_getconfig
from mycatalarm import MyCatAlarm
import webrepl


WEBREPL_PASSWORD = 'cat'
DEFAULT_CONFIG = {'essid': 'MYWIFI',
                  'password': 'MYPASSWORD',
                  'mqtt_enabled': 'false',
                  'mqtt_broker': '127.0.0.1',
                  'mqtt_topic': '/cat_alarm/motion',
                  'mqtt_username': 'username',
                  'mqtt_password': 'password'}


def start_cat_alarm(config):
    wdt = WDT(timeout=30)
    loop = asyncio.get_event_loop()
    button_obj = MyPinIn(pin=14, event_loop=loop)
    pir_objs = MyPinIn(pin=12, event_loop=loop), MyPinIn(pin=13, event_loop=loop)
    cat_alarm = MyCatAlarm(button=button_obj, pirs=pir_objs, event_loop=loop, config=config, wdt=wdt)

    mylogging.basicConfig(level=mylogging.INFO)
    log = mylogging.getLogger(__name__)

    app = mypicoweb.MyPicoWeb(__name__, button_obj=button_obj, cat_alarm=cat_alarm)
    app.add_url_rule('/save', web_save)
    app.add_url_rule('/status', web_status)
    app.add_url_rule('/getconfig', web_getconfig)

    gc.collect()
    app.run(host="0.0.0.0", port=80, log=log, debug=True)


def main():
    # check initially how many click
    clicks = blocking_count_clicks(timeout=5)
    if clicks == 1:
        print('reset configuration')
        blink_int(on_time=1000)
        save_config(DEFAULT_CONFIG)
    stop_all_wifi()
    c = get_config(DEFAULT_CONFIG)
    print('config loaded {}'.format(c))
    wifi_connected = wifi_connect(c['essid'], c['password'])
    if not wifi_connected:
        start_ap()
    if clicks == 2:
        print('starting webrepl using password {}'.format(WEBREPL_PASSWORD))
        blink_int(count=10, on_time=200)
        webrepl.start_foreground()
    else:
        start_cat_alarm(c)
        del c
        gc.collect()


if __name__ == '__main__':
    main()
