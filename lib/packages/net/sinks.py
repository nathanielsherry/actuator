from actuator.components import sink as mod_sink, monitor
import socketserver
import http.server

from actuator.components.decorators import parameter, argument, input, output, allarguments, sink

@parameter('address', 'str', '', 'Address to listen on')
@parameter('port', 'int', 8080, 'Port to listen on')
class WebServerSink(mod_sink.DedicatedThreadSink, mod_sink.OnDemandMixin):

    def make_dedicated(self): 
        return WebServerSink.HTTPServerThread(self)
        
    def set_dedicated_state(self, payload):
        self.set_payload(payload)
    
    def suggest_monitor(self):
        return self.ondemand_monitor
            
    class HTTPServerThread(mod_sink.DedicatedThread):
        def __init__(self, sink):
            super().__init__()
            self._sink = sink
            self._server = None

        #Called when the thread starts, by the thread itself
        def run(self):
            import socketserver
            self._server = WebServerSink.SinkRequestServer((self._sink.params.address, self._sink.params.port), WebServerSink.SinkRequestHandler)
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
            setattr(self, '_sink', sink)
        
        @property        
        def sink(self):
            return getattr(self, '_sink')
        

    class SinkRequestHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            contents = self.server.sink.get_payload()
            self.send_response(200)
            self.send_header("Content-type", "text")
            self.end_headers()
            self.wfile.write(str(contents).encode())
                
                
