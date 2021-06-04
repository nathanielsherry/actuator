#!/usr/bin/python3

from actuator import log, util
from actuator.components import component

def instructions():
    return {
        "outflow": FlowSink
    }
    
    
def build(instruction, kwargs):
    return instructions()[instruction](kwargs)    
    


class Sink(component.Component):
    def perform(self, payload):
        raise Exception("Unimplemented")
    
    def stop(self):
        #By default, a sink does not run any threads
        return
    
    #There are cases where the sink may want to provide
    #its own monitor so that pull-based sink implementations
    #such as a web server may fetch data more effectively
    def custom_monitor(self):
        return None


class OnDemandMixin:
    def __init__(self, *args, **kwargs):
        self._monitor = None
        self._push_payload = None
    
    def get_payload(self):
        if self._monitor:
            return self._monitor.demand()
        else:
            return self._push_payload
    
    def set_payload(self, payload):
        self._push_payload = payload
    
    @property
    def ondemand_monitor(self):
        from actuator.components import monitor
        if not self._monitor: 
            self._monitor = monitor.OnDemandMonitor({})
        return self._monitor

class ToggleSink(Sink):
    def perform(self, payload):
        return self.toggle(payload)
    def toggle(self, state):
        raise Exception("Unimplemented")

class RunnerSink(Sink):
    def perform(self, payload):
        self.run()
    def run(self):
        raise Exception("Unimplemented")


class FlowSink(Sink, OnDemandMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._target_name = args[0]
        
    @property
    def target_name(self): return self._target_name
    
    def custom_monitor(self):
        return self.ondemand_monitor
    
    def perform(self, payload):
        self.set_payload(payload)


        
        



import threading
class DedicatedThreadSink(Sink):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._dedicated = None

    def perform(self, payload):
        if not self._dedicated:
            self._dedicated = self.make_dedicated()
            self.dedicated.start()
        self.set_dedicated_state(payload)

    @property
    def dedicated(self):
        return self._dedicated

    def stop_dedicated(self):
        self.dedicated.terminate()

    def stop(self):
        self.stop_dedicated()

    def make_dedicated(self): raise Exception("Unimplemented")
    def set_dedicated_state(self, kwargs): raise Exception("Unimplemented")


class DedicatedThread(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self._terminated = threading.Event()
    
    #Called when the thread starts by the thread itself
    #the method should call self._terminated.set() at the end to signal
    #that it has completed
    def run(self): raise Exception("Unimplemented")
    
    #Called when the thread is asked to end, not by the thread itself.
    #Should call self._terminated.wait() 
    def terminate(self): raise Exception("Unimplemented")







    
    


        

