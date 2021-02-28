try:
    from machine import Pin
except ImportError:
    from mymocks import *
import utime


def blink_int(led_pin=2, count=1, on_time=500):
    for _ in range(count):
        led = Pin(led_pin, Pin.OUT)
        led.value(False)
        utime.sleep_ms(on_time)
        led.value(True)
