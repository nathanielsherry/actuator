from actuator.components import sink
from actuator import util

import subprocess, threading


#Runs an arbitrary shell command on activation
class Shell(sink.Sink):
    def initialise(self, *args, **kwargs):
        super().initialise(*args, **kwargs)
        self._args = args
        self._shell = False
        if len(self._args) == 1 and ' ' in self._args[0]:
            self._shell = True
            
    def perform(self, payload):
        import subprocess
        payload = str(payload)
        subprocess.run(self._args, text=True, input=payload, shell=self._shell)

#Runs an arbitrary shell command on activation
class ShellRunner(sink.RunnerSink):
    def initialise(self, *args, **kwargs):
        super().initialise(*args, **kwargs)
        self._args = args
        self._shell = False
        if len(self._args) == 1 and ' ' in self._args[0]:
            self._shell = True
            
    def run(self):
        import subprocess
        subprocess.run(self._args, shell=self._shell)

class Stdout(sink.Sink):
    def perform(self, payload):          
        if isinstance(payload, str):
            print(payload, flush=True)
        else:
            import pprint
            pp = pprint.PrettyPrinter(indent=4)
            pp.pprint(payload)

class StdoutIf(sink.ToggleSink):
    def initialise(self, *args, **kwargs):
        super().initialise(*args, **kwargs)
        self._true_msg = kwargs['true']
        self._false_msg = kwargs['false']
        
    def toggle(self, state):
        msg = self._true_msg if state else self._false_msg
        if msg: print(msg, flush=True)
      
     
class StdoutMsg(sink.RunnerSink):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._msg = kwargs.get('msg', 'message')
    def run(self):
        print(self._msg, flush=True)


class JsonSink(sink.Sink):
    def perform(self, payload):
        import json
        print(json.dumps(payload), flush=True)


class Curses(sink.DedicatedThreadSink):   
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._monitor = None
   
    def make_dedicated(self): 
        return Curses.ScreenThread()
    
    def set_dedicated_state(self, payload): 
        self.dedicated.set_buffer(payload)
    
    def custom_monitor(self):
        from actuator import monitor
        if not self._monitor: 
            self._monitor = monitor.IntervalMonitor({}) 
        return self._monitor
    
    class ScreenThread(sink.DedicatedThread):
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
