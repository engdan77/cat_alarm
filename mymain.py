"""cat alarm: project for scaring cats"""

__license__ = "MIT"
__version__ = "0.0.1"
__email__ = "daniel@engvalls.eu"

from mymocks import init_mocks
init_mocks()

import gc
import mylogging
import mypicoweb
import uasyncio as asyncio
from mypinin import MyPinIn, MyDHT
from myconfig import get_config, save_config
from mywatchdog import WDT
from myled import blink_int
from mywifi import stop_all_wifi, start_ap, wifi_connect
from webresources import web_status, web_index, web_honk, web_change_state
from mycatalarm import MyCatAlarm

try:
    import webrepl
    from ntptime import settime
except ImportError:
    from mymocks import *


WEBREPL_PASSWORD = 'cat'
DEFAULT_CONFIG = {'essid': 'MYWIFI',
                  'password': 'MYPASSWORD',
                  'mqtt_enabled': 'false',
                  'mqtt_broker': '127.0.0.1',
                  'mqtt_topic': '/cat_alarm/motion',
                  'mqtt_username': 'username',
                  'mqtt_password': 'password',
                  'enable': False,
                  'hours': '9-15'}


def global_exception_handler(loop, context):
    print('global exception handler ', context)


def start_cat_alarm(config):
    wdt = WDT(timeout=30)
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(global_exception_handler)
    dht_obj = MyDHT(13, dht_type=DHT22, event_loop=loop)
    button_obj = MyPinIn(pin=14, pull=Pin.PULL_UP, active_state=0, event_loop=loop)
    pir_objs = MyPinIn(pin=12, bounce_ms=5000, event_loop=loop), MyPinIn(pin=4, bounce_ms=5000, event_loop=loop)
    cat_alarm = MyCatAlarm(button=button_obj, pirs=pir_objs, dht=dht_obj, event_loop=loop, config=config, wdt=wdt)

    mylogging.basicConfig(level=mylogging.INFO)
    log = mylogging.getLogger(__name__)

    app = mypicoweb.MyPicoWeb(__name__, button_obj=button_obj, cat_alarm=cat_alarm)
    app.add_url_rule('/', web_index)
    app.add_url_rule('/honk', web_honk)
    app.add_url_rule('/change', web_change_state)
    app.add_url_rule('/status', web_status)

    gc.collect()
    app.run(host="0.0.0.0", port=80, log=log, debug=True)


def main():
    print('start')
    settime()

    # clicks = blocking_count_clicks(timeout=5)
    clicks = 0
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
