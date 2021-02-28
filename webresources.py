import gc
import ujson
try:
    from machine import reset
except ImportError:
    from mymocks import *
import mypicoweb
from myconfig import get_config, save_config
from urltools import query_params_to_dict


async def w(writer_obj, data):
    """Special handler to support StreamWriter on ESP or other"""
    print("writing new: {}".format(data))
    import sys
    if 'esp' not in sys.platform:
        writer_obj.write(data.encode())
        await writer_obj.drain()
    else:
        print('write esp')
        writer_obj.write(data)
        await writer_obj.drain()
        # writer_obj.awrite(data)


def web_index(req, resp, **kwargs):
    yield from mypicoweb.start_response(resp)
    yield from resp.awrite(index.data())
    gc.collect()


def web_jquery(req, resp, **kwargs):
    gc.collect()
    yield from mypicoweb.start_response(resp)
    yield from resp.awrite(jquery.data())
    gc.collect()


async def web_status(req, resp, **kwargs):
    print('start web_status')
    gc.collect()
    cat_alarm = kwargs.get('cat_alarm', None)
    print('start response')
    print(resp)
    await mypicoweb.start_response(resp)
    print('start response complete')
    params = req.qs
    print('parsing query param {}'.format(params))
    command, value = params.split('=') if len(params) > 1 else (None, None)
    s = None
    if command == 'state':
        print('turning relay {}'.format(value))
        s = {'on': True, 'off': False}.get(value, None)
        # cat_alarm.switch_state(s)
    return_data = {'status': s, 'params': str(params)}
    print(return_data)
    await w(resp, ujson.dumps(return_data))


def web_save(req, resp, **kwargs):
    yield from mypicoweb.start_response(resp)
    params = query_params_to_dict(req.qs)
    mqtt_enabled = 'mqtt_enabled' in params
    params['mqtt_enabled'] = mqtt_enabled
    print('saving configuration {}'.format(params))
    save_config(params)
    yield from resp.awrite('''<html>
    <body style="background-color:blue;">
    <centrer><p>Configuration saved, rebooting...</p></center>
    </body>
    </html>''')
    reset()


def web_getconfig(req, resp, **kwargs):
    default_config = kwargs.get('config', None)
    gc.collect()
    yield from mypicoweb.start_response(resp)
    c = get_config(default_config)
    print('config loaded {}'.format(c))
    j = ujson.dumps(c)
    yield from resp.awrite(j)
