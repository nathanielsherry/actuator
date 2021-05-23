from actuator import sink, monitor
import socketserver
import http.server

class WebServerSink(sink.DedicatedThreadSink):
    
    def __init__(self, config):
        super().__init__(config)
        self._port = int(config.get('port', '8080'))
        self._address = config.get('address', '')
        self._monitor = None
        self._pushstate = None
    
    def makededicated(self): 
        return WebServerSink.HTTPServerThread(self)
        
    def setdedicatedstate(self, kwargs):
        self._pushstate = kwargs
    
    def custom_monitor(self):
        if not self._monitor: 
            self._monitor = monitor.OnDemandMonitor({}) 
        return self._monitor
    
    def get_payload(self):
        if self._monitor:
            return self._monitor.demand()
        else:
            return self._pushstate
        
    class HTTPServerThread(sink.DedicatedThread):
        def __init__(self, sink):
            super().__init__()
            self._sink = sink
            self._server = None

        #Called when the thread starts, by the thread itself
        def run(self):
            import socketserver
            self._server = WebServerSink.SinkRequestServer((self._sink._address, self._sink._port), WebServerSink.SinkRequestHandler)
            self._server.set_payload_fn(lambda: self._sink.get_payload())
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
        
        def set_payload_fn(self, fn):
            setattr(self, 'sink_payload_fn', fn)
                    
        def get_sink_payload(self):
            return getattr(self, 'sink_payload_fn')()
        

    class SinkRequestHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            contents = self.server.get_sink_payload()
            self.send_response(200)
            self.send_header("Content-type", "text")
            self.end_headers()
            self.wfile.write(str(contents).encode())
                
                
