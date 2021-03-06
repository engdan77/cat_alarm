try:
    import network
except ImportError:
    from mymocks import *
import utime

import uselect
import uctypes
import usocket
import ustruct
import urandom
import uasyncio as asyncio
from ntptime import settime
from myled import async_blink_int


class MyWifi:
    def __init__(self, ssid, password, event_loop=None, led_pin=None, poll_interval=None, max_disconnect=30):
        if poll_interval is None:
            poll_interval = {True: 60, False: 20}
        self.max_disconnect = max_disconnect
        self.ssid = ssid
        self.password = password
        self.led_pin = led_pin
        self.connected = False
        self.poll_interval = poll_interval
        stop_all_wifi()
        self.sta_if = wifi_connect(self.ssid, self.password, return_network=True)
        if event_loop:
            event_loop.create_task(self.check_changes())

    async def check_changes(self):
        disconnect_count = 0
        while True:
            await asyncio.sleep(self.poll_interval[self.connected])
            ip, subnet, gateway, dns = self.sta_if.ifconfig()
            print('attempt to ping')
            try:
                _, recv = ping(gateway, count=3)
            except OSError:
                print('ping failed, trying again')
                recv = 0
            connected_before = self.connected
            self.connected = bool(recv)
            print('wifi connected', self.connected)
            if self.led_pin:
                t = {True: (1, 1000), False: (20, 300)}
                await async_blink_int(self.led_pin, *t[self.connected])

            if not self.connected:
                disconnect_count += 1
            else:
                disconnect_count = 0
            print('fail connect wifi', disconnect_count)
            if disconnect_count >= self.max_disconnect:
                print('starting ap mode')
                stop_all_wifi()
                start_ap('cat_alarm')
                break

            if not connected_before and self.connected:
                print('reconnected wifi and setup time')
                try:
                    settime()
                except OSError:
                    print('unable to set time')


def stop_all_wifi():
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(False)
    ap = network.WLAN(network.AP_IF)
    ap.active(False)


def start_ap(ssid='my_ssid'):
    ap = network.WLAN(network.AP_IF)
    utime.sleep(1)
    ap.active(True)
    ap.config(essid=ssid, authmode=network.AUTH_OPEN)
    print('AP mode started')
    print(ap.ifconfig())
    utime.sleep(1)


def wifi_connect(ssid, password, return_network=False, attempts=30):
    connected = False
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(False)
    if not sta_if.isconnected():
        sta_if.active(True)
        sta_if.connect(ssid, password)
        print('connecting to network..., pause 3 sec')
        utime.sleep(3)
        for i in range(1, attempts):
            print('attempt {}'.format(i))
            utime.sleep(1)
            if sta_if.isconnected():
                connected = True
                break
        if not connected:
            sta_if.active(False)
    else:
        connected = True
    if connected:
        utime.sleep(1)
        print('network config:', sta_if.ifconfig())
    if return_network:
        return sta_if
    return connected


# ??Ping (MicroPing) for MicroPython
def randint(min_, max_):
    span = max_ - min_ + 1
    div = 0x3fffffff // span
    offset = urandom.getrandbits(30) // div
    val = min_ + offset
    return val


def checksum(data):
    if len(data) & 0x1:  # Odd number of bytes
        data += b'\0'
    cs = 0
    for pos in range(0, len(data), 2):
        b1 = data[pos]
        b2 = data[pos + 1]
        cs += (b1 << 8) + b2
    while cs >= 0x10000:
        cs = (cs & 0xffff) + (cs >> 16)
    cs = ~cs & 0xffff
    return cs


def ping(host, count=1, timeout=1000, interval=10, quiet=False, size=64):
    # prepare packet
    assert size >= 16, "pkt size too small"
    pkt = b'Q'*size
    pkt_desc = {
        "type": uctypes.UINT8 | 0,
        "code": uctypes.UINT8 | 1,
        "checksum": uctypes.UINT16 | 2,
        "id": uctypes.UINT16 | 4,
        "seq": uctypes.INT16 | 6,
        "timestamp": uctypes.UINT64 | 8,
    }  # packet header descriptor
    h = uctypes.struct(uctypes.addressof(pkt), pkt_desc, uctypes.BIG_ENDIAN)
    h.type = 8  # ICMP_ECHO_REQUEST
    h.code = 0
    h.checksum = 0
    h.id = randint(0, 65535)
    h.seq = 1

    # init socket
    sock = usocket.socket(usocket.AF_INET, usocket.SOCK_RAW, 1)
    sock.setblocking(0)
    sock.settimeout(timeout/1000)
    addr = usocket.getaddrinfo(host, 1)[0][-1][0]  # ip address
    sock.connect((addr, 1))
    not quiet and print("PING %s (%s): %u data bytes" % (host, addr, len(pkt)))
    seqs = list(range(1, count+1))  # [1,2,...,count]
    c = 1
    t = 0
    n_trans = 0
    n_recv = 0
    finish = False
    while t < timeout:
        if t == interval and c <= count:
            # send packet
            h.checksum = 0
            h.seq = c
            h.timestamp = utime.ticks_us()
            h.checksum = checksum(pkt)
            if sock.send(pkt) == size:
                n_trans += 1
                t = 0  # reset timeout
            else:
                seqs.remove(c)
            c += 1
        # recv packet
        while 1:
            socks, _, _ = uselect.select([sock], [], [], 0)
            if socks:
                resp = socks[0].recv(4096)
                resp_mv = memoryview(resp)
                h2 = uctypes.struct(uctypes.addressof(resp_mv[20:]), pkt_desc, uctypes.BIG_ENDIAN)
                # TODO: validate checksum (optional)
                seq = h2.seq
                if h2.type == 0 and h2.id == h.id and (seq in seqs):  # 0: ICMP_ECHO_REPLY
                    t_elapsed = (utime.ticks_us()-h2.timestamp) / 1000
                    ttl = ustruct.unpack('!B', resp_mv[8:9])[0]  # time-to-live
                    n_recv += 1
                    not quiet and print("%u bytes from %s: icmp_seq=%u, ttl=%u, time=%f ms" % (len(resp), addr, seq, ttl, t_elapsed))
                    seqs.remove(seq)
                    if len(seqs) == 0:
                        finish = True
                        break
            else:
                break
        if finish:
            break
        utime.sleep_ms(1)
        t += 1
    # close
    sock.close()
    not quiet and print("%u packets transmitted, %u packets received" % (n_trans, n_recv))
    return n_trans, n_recv
