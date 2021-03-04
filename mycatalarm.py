import utime
import sys
if 'esp' in sys.platform:
    from machine import Pin
else:
    from mymocks import *
import uasyncio as asyncio
from mymqtt import publish
import time


def zpad(s):
    if len(str(s)) < 2:
        s = '0{}'.format(s)
    return s


def get_date():
    y, month, day, h, m, *_ = time.localtime()
    h += 1
    if h > 24:
        h = 1
    return '{}/{} {}:{}'.format(day, month, zpad(h), zpad(m))


def get_alarm_time(c=None):
    _, _, _, h, m, *_ = time.localtime()
    if not c:
        return None, h, m
    h += 1
    if h > 24:
        h = 1
    f, t = c['hours'].split('-')
    between = int(f) < h < int(t)
    return between, zpad(h), zpad(m)


class MyCatAlarm:
    def __init__(self,
                 relay_pin=5,
                 led_pin=2,
                 button=None,
                 pirs=[],
                 dht=None,
                 event_loop=None,
                 config=None,
                 wdt=None):
        self.motions = []
        self.wdt = wdt
        self.relay = Pin(relay_pin, Pin.OUT)
        self.led = Pin(led_pin, Pin.OUT)
        self.led.value(True)
        self.button = button
        self.pirs = pirs
        self.dht = dht
        self.state = False
        self.config = config
        self.mqtt_enabled = config.get('mqtt_enabled', False)
        self.mqtt_broker = config.get('mqtt_broker', None)
        self.mqtt_topic = config.get('mqtt_topic').encode()
        self.mqtt_username = config.get('mqtt_username', None)
        self.mqtt_password = config.get('mqtt_password', None)
        if event_loop:
            event_loop.create_task(self.check_motions())
        if self.mqtt_enabled:
            # publish MQTT if enabled
            publish('cat_alarm_client',
                    self.mqtt_broker,
                    '/notification/message',
                    'cat_alarm_started',
                    self.mqtt_username,
                    self.mqtt_password)
        print("cat alarm")

    async def check_motions(self, sleep_ms=500, button_time_secs=1, idle_time=8000):
        while True:
            await asyncio.sleep_ms(sleep_ms)
            between, h, m = get_alarm_time(self.config)
            enabled = self.config.get('enable', False)
            if any([self.button.active, any([p.active for p in self.pirs])]):
                print('movement detected')
                if enabled and between:
                    await self.honk()
                await asyncio.sleep(button_time_secs)

                if self.mqtt_enabled:
                    message = 'motion'
                    # publish MQTT if enabled
                    print('publishing {} to broker {} topic {}'.format(message, self.mqtt_broker, self.mqtt_topic))
                    publish(b'cat_alarm_client',
                            self.mqtt_broker,
                            self.mqtt_topic,
                            message,
                            self.mqtt_username,
                            self.mqtt_password)
                print('pausing until can be triggered again')
                await asyncio.sleep_ms(idle_time)
            if self.wdt:
                self.wdt.feed()

    async def honk(self, honk_time=1500):
        self.relay.value(True)
        print("honk started")
        await asyncio.sleep_ms(honk_time)
        print("honk stopped")
        self.relay.value(False)

    def add_motion(self, max=8):
        self.motions.append(get_date())
        if len(self.motions) > max:
            self.motions.pop(0)

    def get_motions(self):
        return reversed(self.motions)
