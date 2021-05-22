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
class NCursesAction(Toggle):
    
    def __init__(self, config):
        super().__init__(config)
        self._screen = None

    def toggle(self, state):
        if not self._screen:
            self._screen = NCursesAction.ScreenThread()
            self._screen.start()
            util.add_shutdown_hook(lambda: self._screen.terminate())
            
        self._screen.set_buffer(str(state))
        
    
    class ScreenThread(threading.Thread):
        def __init__(self):
            super().__init__()
            self._buffer = ""
            self._event = threading.Event()
            self._screen = None
            self._terminating = False
            self._terminated = threading.Event()
        
        @property
        def screen(self): return self._screen
        
        @property
        def buffer(self): return self._buffer
        
        def set_buffer(self, text): 
            self._buffer = text 
            self._event.set()
        
        def terminate(self):
            self._terminating = True
            self._event.set()
            self._terminated.wait()

        
        #Called when the thread starts
        def run(self):
            import curses
            curses.wrapper(lambda scr: self.runscreen(scr))
            self._terminated.set()
            
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
    
    


