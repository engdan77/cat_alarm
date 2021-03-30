import gc
from mycatalarm import get_alarm_time
try:
    from machine import reset
    import ujson
    import machine
except ImportError:
    from mymocks import *
import mypicoweb
import webrepl
from myconfig import get_config, save_config


def unquote(string):
    """unquote('abc%20def') -> b'abc def'."""
    _hextobyte_cache = {}
    # Note: strings are encoded as UTF-8. This is only an issue if it contains
    # unescaped non-ASCII characters, which URIs should not.
    if not string:
        return b''
    if isinstance(string, str):
        string = string.encode('utf-8')
    bits = string.split(b'%')
    if len(bits) == 1:
        return string
    res = [bits[0]]
    append = res.append
    for item in bits[1:]:
        try:
            code = item[:2]
            char = _hextobyte_cache.get(code)
            if char is None:
                char = _hextobyte_cache[code] = bytes([int(code, 16)])
            append(char)
            append(item[2:])
        except KeyError:
            append(b'%')
            append(item)
    return b''.join(res)


def query_params_to_dict(input_params):
    params = {x[0]: unquote(x[1])
              for x in
              [x.split("=") for x in input_params.split("&")]
              }
    return params


async def w(writer_obj, data):
    """Special handler to support StreamWriter on ESP or other"""
    print("writing (webresources): {}".format(data))
    import sys
    if 'esp' not in sys.platform:
        writer_obj.write(data.encode())
        await writer_obj.drain()
    else:
        writer_obj.write(data)
        await writer_obj.drain()


async def web_index(req, resp, **kwargs):
    my_cat = kwargs['cat_alarm']
    c = get_config()
    between, h, m = get_alarm_time(c)
    await mypicoweb.start_response(resp)
    html = '<html>'
    html += '<body style="background-color:black;">'
    html += '<p style="color:white;"><b><u>Daniels Cat Alarm</u><b></p>'
    html += '<p style="color:white;">Temp (humidity): {} ({})</p>'.format(my_cat.dht.temp, my_cat.dht.humid)
    html += '<p style="color:white;">Time: {}:{}</p>'.format(h, m)
    html += '<p style="color:white;">Enabled: {}</p>'.format(c['enable'])
    html += '<p style="color:white;">Between hours: {} ({})</p>'.format(c['hours'], between)
    html += """<input type=button onClick="parent.location='honk'"
 value='HONK!!!'>"""
    html += """<input type=button onClick="parent.location='change?state=on'"value='Turn ON'>"""
    html += """<input type=button onClick="parent.location='change?state=off'"value='Turn OFF'>"""
    html += """<input type=button onClick="parent.location='reboot'" value='Reboot'>"""
    html += """<input type=button onClick="parent.location='webrepl'" value='Debug'>"""
    html += """<input type=button onClick="parent.location='config'" value='Configure'>"""
    html += """<br><br><img src="https://www.clipartmax.com/png/full/275-2751327_illustration-of-a-cartoon-scared-cat-cartoon-scared-cat-transparent.png", height=200, width=200>"""
    html += '<p style="color:white;">Motions detected</p>'
    for _ in reversed(my_cat.motions):
        html += '<p style="color:white;">{}</p>'.format(_)
    html += '</html>'
    await w(resp, html)
    gc.collect()


async def web_reboot(req, resp, **kwargs):
    await mypicoweb.start_response(resp)
    html = '<html>'
    html += '<meta http-equiv="refresh" content="10; URL=/" />'
    html += '<body style="background-color:black;">'
    html += '<p style="color:white;">Rebooting !!</p>'
    html += '</html>'
    await w(resp, html)
    print('rebooting')
    machine.reset()


async def web_repl(req, resp, **kwargs):
    await mypicoweb.start_response(resp)
    html = '<html>'
    html += '<meta http-equiv="refresh" content="10; URL=/" />'
    html += '<body style="background-color:black;">'
    html += '<p style="color:white;">Starting REPL !!</p>'
    html += '</html>'
    await w(resp, html)
    print('start webrepl')
    webrepl.start_foreground()


async def web_honk(req, resp, **kwargs):
    await mypicoweb.start_response(resp)
    html = '<html>'
    html += '<meta http-equiv="refresh" content="3; URL=/" />'
    html += '<body style="background-color:black;">'
    html += '<p style="color:white;">HONK HONK !!</p>'
    html += '</html>'
    await w(resp, html)
    my_cat = kwargs['cat_alarm']
    await my_cat.honk()
    gc.collect()


async def web_change_state(req, resp, **kwargs):
    my_cat = kwargs['cat_alarm']
    await mypicoweb.start_response(resp)
    params = req.qs
    command, value = params.split('=') if len(params) > 1 else (None, None)
    s = None
    if command == 'state':
        print('turning relay {}'.format(value))
        s = {'on': True, 'off': False}.get(value, None)
    c = get_config()
    c['enable'] = s
    my_cat.config['enable'] = s
    save_config(c)

    html = '<html>'
    html += '<meta http-equiv="refresh" content="3; URL=/" />'
    html += '<body style="background-color:black;">'
    html += '<p style="color:white;">Enabled: {}</p>'.format(s)
    html += '</html>'
    await w(resp, html)
    gc.collect()


async def web_status(req, resp, **kwargs):
    gc.collect()
    await mypicoweb.start_response(resp)
    params = req.qs
    print('parsing query param {}'.format(params))
    command, value = params.split('=') if len(params) > 1 else (None, None)
    s = None
    if command == 'state':
        print('turning relay {}'.format(value))
        s = {'on': True, 'off': False}.get(value, None)
        # cat_alarm.switch_state(s)
    return_data = {'status': s, 'params': str(params)}
    await w(resp, ujson.dumps(return_data))


async def web_save_config(req, resp, **kwargs):
    await mypicoweb.start_response(resp)
    params = query_params_to_dict(req.qs)
    print('saving configuration {}'.format(params))
    save_config(params)
    await w(resp, '''<html>
    <body style="background-color:black;">
    <center><p>Configuration saved, rebooting...</p></center>
    </body>
    </html>''')
    reset()


async def web_get_config(req, resp, **kwargs):
    default_config = kwargs.get('config', None)
    gc.collect()
    await mypicoweb.start_response(resp)
    c = get_config(default_config)
    print('config loaded {}'.format(c))
    j = ujson.dumps(c)
    await w(resp, j)


async def web_config(req, resp, **kwargs):
    await mypicoweb.start_response(resp)
    c = get_config()
    print(c)

    h = ''

    def r(input_text):
        input_text = {True: "1", False: "0"}.get(input_text, input_text)
        return input_text.replace('_', ' ').capitalize()
    for k, v in c.items():
        if str(v).lower() in ('true', 'false'):
            h += '<input type="hidden" value="0" name="{}">'.format(k)
            h += '<p style="color:white;">{}: <input type="checkbox" value="1" name="{}" {}></p>'.format(r(k), k, 'checked' if v else '')
        else:
            h += '<p style="color:white;">{}: <input type="text" name="{}" value="{}"></input><br></p>'.format(r(k), k, v)

    await w(resp, '''<html>
    <body style="background-color:black;">
    <form action="/save_config">
    {}
    <input type="submit" value="Save">
    <input type="button" onclick="window.location.href='/';" value=Back />
    </form>
    </body>
    </html>'''.format(h))