#!/usr/bin/python3

from actuator import log, util

def instructions():
    return {
        "systemd": SystemdToggle,
        "printif": PrintIf,
        "printmsg": PrintRunner,
        "print": Print,
    }
    
    
def build(instruction, kwargs):
    return instructions()[instruction](kwargs)    
    


class Sink(util.BaseClass):
    def __init__(self, config):
        super().__init__(config)
        
    def perform(self, **kwargs):
        raise Exception("Unimplemented")

class ToggleSink(Sink):
    def perform(self, **kwargs):
        return self.toggle(kwargs['state'])
    def toggle(self, state):
        raise Exception("Unimplemented")

class RunnerSink(Sink):
    def perform(self, **kwargs):
        self.run()
    def run(self):
        raise Exception("Unimplemented")




        
        
class SystemdToggle(ToggleSink):
    def __init__(self, config):
        self._service = config['service']
        
    def toggle(self, state):
        import subprocess
        subprocess.run(["systemctl", "start" if state == True else "stop", self._service])
        
        
       
class Print(Sink):
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

class PrintIf(ToggleSink):
    def __init__(self, config):
        self._true_msg = config['true']
        self._false_msg = config['false']
        
    def toggle(self, state):
        msg = self._true_msg if state else self._false_msg
        if msg: print(msg)
      
class PrintRunner(RunnerSink):
    def __init__(self, config):
        super().__init__(config)
        self._msg = config.get('msg', 'message')
    def run(self):
        print(self._msg, flush=True)
        





import threading
class DedicatedThreadSink(Sink):
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







    
    


        

