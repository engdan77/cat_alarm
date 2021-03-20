from mymocks import shall_mock
shall_mock()

from machine import Pin
from dht import DHT22
from ucollections import deque
import uasyncio as asyncio
import utime
from myled import blink_int


class MyPinIn:
    def __init__(self, pin=14, pull=None, active_state=1, bounce_ms=1000, event_loop=None):
        self.active_queue = deque((), 10)
        self.pin = pin
        self.pull = pull
        self.active_state = active_state
        self.bounce_ms = bounce_ms
        if event_loop:
            event_loop.create_task(self.check_changes())

    async def check_changes(self, sleep_ms=300):
        while True:
            await asyncio.sleep_ms(sleep_ms)
            p = Pin(self.pin, Pin.IN, self.pull)
            if p.value() is self.active_state:
                self.active_queue.append(True)
                print('pin in active', str(self.pin))
                await asyncio.sleep_ms(self.bounce_ms)

    async def drain_queue(self, sleep_ms=50):
        while True:
            try:
                self.active_queue.popleft()
            except (ValueError, IndexError):
                print('draining complete')
                break
            except Exception:
                print('other error while draining')
                break
                asyncio.sleep_ms(sleep_ms)

    @property
    def active(self):
        try:
            return self.active_queue.popleft()
        except (ValueError, IndexError):
            return False


def blocking_count_clicks(button_pin=14, timeout=5, debounce_ms=5, sleep_ms=10):
    press_count = 0
    number_iterations = (timeout * 1000) / sleep_ms
    for _ in range(int(number_iterations)):
        p = Pin(button_pin, Pin.IN, Pin.PULL_UP)
        print(p.value())
        if bool(p.value()) is False:
            being_pressed = []
            for d in range(20):
                being_pressed.append(bool(p.value()))
                utime.sleep_ms(debounce_ms)
            if not any(being_pressed):
                blink_int()
                press_count += 1
                print('button pressed')
        utime.sleep_ms(sleep_ms)
    return press_count


class MyDHT:
    def __init__(self, pin=13, dht_type=DHT22, event_loop=None):
        self.temp = 0
        self.humid = 0
        self.pin = pin
        self.dht_type = dht_type
        if event_loop:
            event_loop.create_task(self.check_changes())

    async def check_changes(self, sleep_ms=5000):
        while True:
            await asyncio.sleep_ms(sleep_ms)
            p = Pin(self.pin)
            d = self.dht_type(p)
            d.measure()
            self.temp = d.temperature()
            self.humid = d.humidity()
