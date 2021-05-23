import subprocess
from actuator import sink


#Runs an arbitrary shell command on activation
class ShellRunner(sink.RunnerSink):
    def __init__(self, config):
        super().__init__(config)
        self._args = config['args']
        self._shell = False
        if len(self._args) == 1 and ' ' in self._args[0]:
            self._shell = True
            
    def run(self):
        import subprocess
        subprocess.run(self._args, shell=self._shell)

class Curses(sink.DedicatedThreadSink):
    def __init__(self, config):
        super().__init__(config)
   
    def makededicated(self): 
        return Curses.ScreenThread()
    
    def setdedicatedstate(self, kwargs): 
        self._dedicated.set_buffer(kwargs)
    
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
