try:
    from machine import Pin
except ImportError:
    from mymocks import *
from ucollections import deque
import uasyncio as asyncio
import utime
from myled import blink_int


class MyPinIn:
    def __init__(self, pin=14, pull=Pin.PULL_UP, event_loop=None):
        self.active_queue = deque((), 10)
        self.pin = pin
        self.pull = pull
        if event_loop:
            event_loop.create_task(self.check_low())

    async def check_low(self, sleep_ms=300, bounce_ms=1000):
        while True:
            await asyncio.sleep_ms(sleep_ms)
            p = Pin(self.pin, Pin.IN, self.pull)
            if bool(p.value()) is False:
                self.active_queue.append(True)
                print(self.pin, ' pulled ', self.pull)
                await asyncio.sleep_ms(bounce_ms)

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
