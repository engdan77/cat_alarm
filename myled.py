try:
    from machine import Pin
except ImportError:
    from mymocks import *
import utime
import uasyncio as asyncio


def pin_change(pin, state):
    led = Pin(pin, Pin.OUT)
    led.value(state)


def blink_int(led_pin=2, count=1, on_time=500):
    for _ in range(count):
        pin_change(led_pin, False)
        utime.sleep_ms(on_time)
        pin_change(led_pin, True)
        utime.sleep_ms(on_time)


async def async_blink_int(led_pin=2, count=1, on_time=500):
    for _ in range(count):
        pin_change(led_pin, False)
        asyncio.sleep_ms(on_time)
        pin_change(led_pin, True)
        asyncio.sleep_ms(on_time)
