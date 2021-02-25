import utime
from machine import Pin
import uasyncio as asyncio
from mymqtt import publish


class MyCatAlarm:
    def __init__(self,
                 relay_pin=12,
                 led_pin=2,
                 button=None,
                 pirs=[],
                 event_loop=None,
                 config=None,
                 wdt=None):
        self.wdt = wdt
        self.relay = Pin(relay_pin, Pin.OUT)
        self.led = Pin(led_pin, Pin.OUT)
        self.led(True)
        self.button = button
        self.pirs = pirs
        self.state = False
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

    async def check_motions(self, sleep_ms=500, button_time_secs=1):
        while True:
            await asyncio.sleep_ms(sleep_ms)
            if any([self.button.active, any([p.active for p in self.pirs])]):
                print('honk')
                await self.honk()
                await asyncio.sleep(button_time_secs)

                if self.mqtt_enabled:
                    message = 'honk'
                    # publish MQTT if enabled
                    print('publishing {} to broker {} topic {}'.format(message, self.mqtt_broker, self.mqtt_topic))
                    publish(b'cat_alarm_client',
                            self.mqtt_broker,
                            self.mqtt_topic,
                            message,
                            self.mqtt_username,
                            self.mqtt_password)
            if self.wdt:
                self.wdt.feed()

    async def honk(self, honk_time=1500):
        self.relay.value(True)
        print("honk started")
        await asyncio.sleep_ms(honk_time)
        print("honk stopped")

