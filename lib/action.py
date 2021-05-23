#!/usr/bin/python3

from actuator import log, util, parser

def instructions():
    return {
        "systemd": SystemdToggle,
        "sh": ShellRunner,
        "printif": PrintIf,
        "printmsg": PrintRunner,
        "print": PrintAction,
        "curses": NCursesAction,
        "webserver": WebServerAction,
    }
    
    
def build(instruction, kwargs):
    return instructions()[instruction](kwargs)    
    


class Action(util.BaseClass):
    def __init__(self, config):
        super().__init__(config)
        
    def perform(self, **kwargs):
        raise Exception("Unimplemented")

class Toggle(Action):
    def perform(self, **kwargs):
        return self.toggle(kwargs['state'])
    def toggle(self, state):
        raise Exception("Unimplemented")

class Runner(Action):
    def perform(self, **kwargs):
        self.run()
    def run(self):
        raise Exception("Unimplemented")



#Runs an arbitrary shell command on activation
class ShellRunner(Runner):
    def __init__(self, config):
        super().__init__(config)
        self._args = config['args']
        self._shell = False
        if len(self._args) == 1 and ' ' in self._args[0]:
            self._shell = True
            
    def run(self):
        import subprocess
        subprocess.run(self._args, shell=self._shell)
        
        
class SystemdToggle(Toggle):
    def __init__(self, config):
        self._service = config['service']
        
    def toggle(self, state):
        import subprocess
        subprocess.run(["systemctl", "start" if state == True else "stop", self._service])
        
        
       
class PrintAction(Action):
    def __init__(self, config):
        super().__init__(config)
    def perform(self, **kwargs):
        if len(kwargs) == 1 and 'state' in kwargs:
            kwargs = kwargs['state']
            
        if isinstance(kwargs, str):
            print(kwargs)
        else:
            import pprint
            pp = pprint.PrettyPrinter(indent=4)
            pp.pprint(kwargs)

class PrintIf(Toggle):
    def __init__(self, config):
        self._true_msg = config['true']
        self._false_msg = config['false']
        
    def toggle(self, state):
        msg = self._true_msg if state else self._false_msg
        if msg: print(msg)
      
class PrintRunner(Runner):
    def __init__(self, config):
        super().__init__(config)
        self._msg = config.get('msg', 'message')
    def run(self):
        print(self._msg, flush=True)
        





import threading
class DedicatedThreadAction(Action):
    def __init__(self, config):
        super().__init__(config)
        self._dedicated = None

    def perform(self, **kwargs):
        if not self._dedicated:
            self._dedicated = self.makededicated()
            self._dedicated.start()
            util.add_shutdown_hook(lambda: self._dedicated.terminate())
        if len(kwargs) == 1 and 'state' in kwargs: kwargs = kwargs['state']
        self.setdedicatedstate(kwargs)

    def makededicated(self): raise Exception("Unimplemented")
    def setdedicatedstate(self, kwargs): raise Exception("Unimplemented")



class DedicatedThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self._terminated = threading.Event()
    
    #Called when the thread starts by the thread itself
    #the method should call self._terminated.set() at the end to signal
    #that it has completed
    def run(self): raise Exception("Unimplemented")
    
    #Called when the thread is asked to end, not by the thread itself.
    #Should call self._terminated.wait() 
    def terminate(self): raise Exception("Unimplemented")






class NCursesAction(DedicatedThreadAction):
    def __init__(self, config):
        super().__init__(config)
   
    def makededicated(self): 
        return NCursesAction.ScreenThread()
    
    def setdedicatedstate(self, kwargs): 
        self._dedicated.set_buffer(kwargs)
    
    class ScreenThread(DedicatedThread):
        def __init__(self):
            super().__init__()
            self._buffer = ""
            self._event = threading.Event()
            self._screen = None
            self._terminating = False

        #Called when the thread starts
        def run(self):
            import curses
            curses.wrapper(lambda scr: self.runscreen(scr))
            self._terminated.set()
        
        #Called when the thread is asked to end
        def terminate(self):
            self._terminating = True
            self._event.set()
            self._terminated.wait()

        
        @property
        def screen(self): return self._screen
        
        @property
        def buffer(self): return self._buffer
        
        def set_buffer(self, text): 
            self._buffer = text 
            self._event.set()
        
            
        #Called by curses.wrapper once the thread starts and the screen is initialised
        def runscreen(self, scr):
            import curses
            curses.use_default_colors()
            self._screen = scr
            while True:
                self._event.wait()
                if self._terminating: return
                self.display()
                self._event.clear()
                
        #Called once everything is set up to write the buffer
        def display(self):
            import socket, datetime
            self.screen.clear()
            y = 1
            x = 2
            timestamp = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
            hostname = socket.gethostname()
            header_left = "Actuator: {}".format(util.get_global('expression', ''))
            header_right = "{}: {}".format(hostname, timestamp)
            x_right = self.screen.getmaxyx()[1]-2-len(header_right)
            self.screen.addstr(y, x, header_left)
            self.screen.addstr(y, x_right, header_right)
            y+= 2
            for line in self.buffer.split("\n"):
                try:
                    self.screen.border()
                    self.screen.addstr(y, x, line)
                except:
                    pass
                y += 1
                
            self.screen.refresh()
    
    


        

class WebServerAction(DedicatedThreadAction):
    import http.server
    import socketserver
    
    def __init__(self, config):
        super().__init__(config)
        self._port = int(config.get('port', '8080'))
        self._address = config.get('address', '')
        
    def makededicated(self): 
        return WebServerAction.HTTPServerThread(self._port, self._address)
        
    def setdedicatedstate(self, kwargs): 
        self._dedicated.set_state(kwargs)
        
    class HTTPServerThread(DedicatedThread):
        def __init__(self, port=8080, address=''):
            super().__init__()
            self._port = port
            self._address = address
            self._server = None

        #Called when the thread starts, by the thread itself
        def run(self):
            import socketserver
            self._server = WebServerAction.ActionRequestServer((self._address, self._port), WebServerAction.ActionRequestHandler)
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
            
            
