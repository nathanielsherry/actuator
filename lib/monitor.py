#!/usr/bin/python3

import time
from actuator import log, util


def instructions():
    return {
        "change": ChangeMonitor,
        "loop": LoopMonitor,
        "start": StartMonitor,
        "true": TrueStateMonitor,
    }
    

def build(instruction, kwargs):
    return instructions()[instruction](kwargs)



class Monitor(util.BaseClass):
    def __init__(self, config):
        super().__init__(config)
        self._state = None
        self._sink = None
        
    def start(self, state, sink):
        raise Exception("Unimplemented")
        

class MonitorDelayMixin:
    def __init__(self, config):
        self._delay = config.get('delay', None)
        if self._delay: 
            self._delay = int(self._delay)
            
    @property
    def delay(self):
        return self._delay
    
#Monitors the result of a State over time, triggering an event (callback) 
#when the value changes, passing the new state as the single argument.
class ChangeMonitor(Monitor, MonitorDelayMixin):
    def __init__(self, config):
        super().__init__(config)

    def start(self, state, sink):
        log.info("Starting {name} with test {test} and sink {sink}".format(name=self.name, test=state, sink=sink))
        last_state = None
        new_state = None
        while True:
            new_state = state.value
            if new_state != last_state:
                log.info("{name} yields '{state}' ({result}), running sink.".format(name=self.name, result="changed" if new_state != last_state else "unchanged", state=util.short_string(new_state)))
                sink.perform(state=new_state)
                last_state = new_state
            time.sleep(self.delay or state.delay)

    

class LoopMonitor(Monitor, MonitorDelayMixin):
    def __init__(self, config):
        super().__init__(config)
    
    def start(self, state, sink):
        while True:
            sink.perform(state=state.value)
            time.sleep(self.delay or state.delay)
            

class TrueStateMonitor(Monitor, MonitorDelayMixin):
    def __init__(self, config):
        super().__init__(config)
        
    def start(self, state, sink):
        while True:
            if state.value == True: sink.perform()
            time.sleep(self.delay or state.delay)

class StartMonitor(Monitor):
    def __init__(self, config):
        super().__init__(config)
        
    def start(self, state, sink):
        sink.perform(state=state.value)
