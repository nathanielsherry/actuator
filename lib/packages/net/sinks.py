from actuator import action
import socketserver
import http.server

class WebServerSink(action.DedicatedThreadAction):
    
    def __init__(self, config):
        super().__init__(config)
        self._port = int(config.get('port', '8080'))
        self._address = config.get('address', '')
        
    def makededicated(self): 
        return WebServerSink.HTTPServerThread(self._port, self._address)
        
    def setdedicatedstate(self, kwargs): 
        self._dedicated.set_state(kwargs)
            
    class HTTPServerThread(action.DedicatedThread):
        def __init__(self, port=8080, address=''):
            super().__init__()
            self._port = port
            self._address = address
            self._server = None

        #Called when the thread starts, by the thread itself
        def run(self):
            import socketserver
            self._server = WebServerSink.ActionRequestServer((self._address, self._port), WebServerSink.ActionRequestHandler)
            self._server.serve_forever(poll_interval=0.25)
            self._server.server_close()
            self._terminated.set()
            
        #Called when the thread is asked to end by some other thread
        def terminate(self):
            self._server.shutdown()
            self._terminated.wait()
        
        def set_state(self, contents):
            import time
            if not self._server: time.sleep(1)
            self._server.set_action_payload(contents)

        
    #Extend TCPServer to act as intermediary between the action and the request handler
    class ActionRequestServer(socketserver.TCPServer):
        
        def set_action_payload(self, payload):
            setattr(self, 'action_payload', payload)
            
        def get_action_payload(self):
            return getattr(self, 'action_payload')
        

    class ActionRequestHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            contents = self.server.get_action_payload()
            self.send_response(200)
            self.send_header("Content-type", "text")
            self.end_headers()
            self.wfile.write(contents.encode())
                
                
