#!/usr/bin/python3

from actuator import log, util

def instructions():
    return {
        "systemd": SystemdToggle,
    }
    
    
def build(instruction, kwargs):
    return instructions()[instruction](kwargs)    
    


class Sink(util.BaseClass):
    def __init__(self, config):
        super().__init__(config)
        
    def perform(self, **kwargs):
        raise Exception("Unimplemented")
    
    #There are cases where the sink may want to provide
    #its own monitor so that pull-based sink implementations
    #such as a web server may fetch data more effectively
    def custom_monitor(self):
        return None

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







    
    


        

