import utime
import picoweb
from picoweb import HTTPRequest, start_response


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


async def c(writer_obj):
    """Special handler to support closing on ESP or other"""
    print(writer_obj)
    writer_obj.close()
    await writer_obj.wait_closed()


class MyPicoWeb(picoweb.WebApp):
    def __init__(self, pkg, routes=None, serve_static=True, **kwargs):
        self.kwargs = kwargs
        super().__init__(pkg, routes, serve_static)

    async def _handle(self, reader, writer):
        if self.debug > 1:
            micropython.mem_info()
        close = True
        req = None
        try:
            request_line = await reader.readline()
            if request_line == b"":
                if self.debug >= 0:
                    self.log.error("%s: EOF on request start" % reader)
                await c(writer)
                return
            req = HTTPRequest()
            request_line = request_line.decode()
            method, path, proto = request_line.split()
            if self.debug >= 0:
                self.log.info('%.3f %s %s "%s %s"' % (utime.time(), req, writer, method, path))
            path = path.split("?", 1)
            qs = ""
            if len(path) > 1:
                qs = path[1]
            path = path[0]
            # Find which mounted subapp (if any) should handle this request
            app = self
            while True:
                found = False
                for subapp in app.mounts:
                    root = subapp.url
                    if path[:len(root)] == root:
                        app = subapp
                        found = True
                        path = path[len(root):]
                        if not path.startswith("/"):
                            path = "/" + path
                        break
                if not found:
                    break
            if not app.inited:
                app.init()
            # Find handler to serve this request in app's url_map
            found = False
            for e in app.url_map:
                pattern = e[0]
                handler = e[1]
                extra = {}
                if len(e) > 2:
                    extra = e[2]

                if path == pattern:
                    found = True
                    break
                elif not isinstance(pattern, str):
                    m = pattern.match(path)
                    if m:
                        req.url_match = m
                        found = True
                        break
            if not found:
                headers_mode = "skip"
            else:
                headers_mode = extra.get("headers", self.headers_mode)

            if headers_mode == "skip":
                while True:
                    l = await reader.readline()
                    if l == b"\r\n":
                        break
            elif headers_mode == "parse":
                req.headers = await self.parse_headers(reader)
            else:
                assert headers_mode == "leave"

            if found:
                req.method = method
                req.path = path
                req.qs = qs
                req.reader = reader
                # My customization to pass temp object
                print('running handler with kwargs {}'.format(self.kwargs))
                close = await handler(req, writer, **self.kwargs)
            else:
                await start_response(writer, status="404")
                await w(writer, "404\r\n")
        except Exception as e:
            if self.debug >= 0:
                self.log.exc(e, "%.3f %s %s %r" % (utime.time(), req, writer, e))
            self.handle_exc(req, writer, e)

        if close is not False:
            await c(writer)

        if __debug__ and self.debug > 1:
            self.log.debug("%.3f %s Finished processing request", utime.time(), req)

    def handle_exc(self, req, resp, e):
        print('exception !!!!')
        print('req: {}'.format(req))
        print('resp: {}'.format(resp))
        print('exception: {}'.format(e))
        yield
