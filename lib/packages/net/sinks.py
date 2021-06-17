from actuator.components import sink, monitor
from actuator.lang.accessor import accessor
import socketserver
import http.server

class WebServerSink(sink.DedicatedThreadSink, sink.OnDemandMixin):
    
    def initialise(self, *args, **kwargs):
        super().initialise(*args, **kwargs)
        self._port = int(kwargs.get('port', '8080'))
        self._address = kwargs.get('address', '')
        self._monitor = None

    def make_dedicated(self): 
        return WebServerSink.HTTPServerThread(self)
        
    def set_dedicated_state(self, payload):
        self.set_payload(payload)
    
    def suggest_monitor(self):
        return self.ondemand_monitor
            
    class HTTPServerThread(sink.DedicatedThread):
        def __init__(self, sink):
            super().__init__()
            self._sink = sink
            self._server = None

        #Called when the thread starts, by the thread itself
        def run(self):
            import socketserver
            self._server = WebServerSink.SinkRequestServer((self._sink._address, self._sink._port), WebServerSink.SinkRequestHandler)
            self._server.set_sink(self._sink)
            self._server.serve_forever(poll_interval=0.25)
            self._server.server_close()
            self._server.socket.close()
            self._terminated.set()
            
        #Called when the thread is asked to end by some other thread
        def terminate(self):
            self._server.shutdown()
            self._terminated.wait()
        
        
    #Extend TCPServer to act as intermediary between the sink and the request handler
    class SinkRequestServer(socketserver.TCPServer):
        allow_reuse_address = True
        
        def set_sink(self, sink):
            setattr(self, 'sink', sink)
            
        def get_sink(self):
            return getattr(self, 'sink')
        

    class SinkRequestHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            from urllib.parse import urlparse
            sink = self.server.get_sink()
            contents = sink.get_payload()
            
            def send_200(payload):
                self.send_response(200)
                self.send_header("Content-type", "text")
                self.end_headers()
                self.wfile.write(str(payload).encode())
            
            def send_404():
                self.send_response(404)
                self.send_header("Content-type", "text")
                self.end_headers()
                self.wfile.write("404: Not Found".encode())
            
            try:
                path = urlparse(self.path).path[1:].split('/')
                path = [p for p in path if p]
                fn = accessor(path)
                contents = fn(contents)
                send_200(contents)
            except IndexError:
                send_404()
                return
                
