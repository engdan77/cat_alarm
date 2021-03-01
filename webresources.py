import gc
import time
try:
    from machine import reset
    import ujson
except ImportError:
    from mymocks import *
import mypicoweb
from myconfig import get_config, save_config


async def w(writer_obj, data):
    """Special handler to support StreamWriter on ESP or other"""
    print("writing: {}".format(data))
    import sys
    if 'esp' not in sys.platform:
        writer_obj.write(data.encode())
        await writer_obj.drain()
    else:
        writer_obj.write(data)
        await writer_obj.drain()


async def web_index(req, resp, **kwargs):
    c = get_config()

    _, _, _, h, m, *_ = time.localtime()
    h += 1
    if h > 24:
        h = 1

    f, t = c['hours'].split('-')
    between = int(f) < h < int(t)

    await mypicoweb.start_response(resp)
    html = '<html>'
    html += '<body style="background-color:black;">'
    html += '<p style="color:white;">Cat Alarm</p>'
    html += '<p style="color:white;">Time: {}:{}</p>'.format(h, m)
    html += '<p style="color:white;">Enabled: {}</p>'.format(c['enable'])
    html += '<p style="color:white;">Between hours: {} ({})</p>'.format(c['hours'], between)
    html += """<input type=button onClick="parent.location='honk'"
 value='HONK!!!'>"""
    html += """<input type=button onClick="parent.location='change?state=on'"value='Turn ON'>"""
    html += """<input type=button onClick="parent.location='change?state=off'"value='Turn OFF'>"""
    html += '</html>'
    await w(resp, html)
    gc.collect()


async def web_honk(req, resp, **kwargs):
    await mypicoweb.start_response(resp)
    html = '<html>'
    html += '<meta http-equiv="refresh" content="3; URL=/" />'
    html += '<body style="background-color:black;">'
    html += '<p style="color:white;">HONK HONK !!</p>'
    html += '</html>'
    await w(resp, html)
    gc.collect()


async def web_change_state(req, resp, **kwargs):
    await mypicoweb.start_response(resp)
    params = req.qs
    command, value = params.split('=') if len(params) > 1 else (None, None)
    s = None
    if command == 'state':
        print('turning relay {}'.format(value))
        s = {'on': True, 'off': False}.get(value, None)
    c = get_config()
    c['enable'] = s
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
    cat_alarm = kwargs.get('cat_alarm', None)
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
