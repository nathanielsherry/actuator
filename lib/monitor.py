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
        self._source = None
        self._sink = None
        
    def start(self, source, sink):
        raise Exception("Unimplemented")
        

class MonitorDelayMixin:
    def __init__(self, config):
        self._delay = config.get('delay', None)
        if self._delay: 
            self._delay = int(self._delay)
            
    @property
    def delay(self):
        return self._delay
    
#Monitors the result of a Source over time, triggering an event (callback) 
#when the value changes, passing the new state as the single argument.
class ChangeMonitor(Monitor, MonitorDelayMixin):
    def __init__(self, config):
        super().__init__(config)

    def start(self, source, sink):
        log.info("Starting {name} with test {source} and sink {sink}".format(name=self.name, source=source, sink=sink))
        last_state = None
        new_state = None
        while True:
            new_state = source.value
            if new_state != last_state:
                log.info("{name} yields '{state}' ({result}), running sink.".format(name=self.name, result="changed" if new_state != last_state else "unchanged", state=util.short_string(new_state)))
                sink.perform(state=new_state)
                last_state = new_state
            time.sleep(self.delay or source.delay)

    
class OnDemandMonitor(Monitor):
    def __init__(self, config):
        super().__init__(config)
        
        
    def start(self, source, sink):
        self._source = source
        self._sink = sink
        #Call sink.perform once in case there's any one-time setup needed
        self._sink.perform(state=self.demand())
        #Block the monitor thread as if we were doing something important
        import time
        while True: time.sleep(1)
        
    def demand(self):
        return self._source.value
        

class LoopMonitor(Monitor, MonitorDelayMixin):
    def __init__(self, config):
        super().__init__(config)
    
    def start(self, source, sink):
        while True:
            sink.perform(state=source.value)
            time.sleep(self.delay or source.delay)
            

class TrueStateMonitor(Monitor, MonitorDelayMixin):
    def __init__(self, config):
        super().__init__(config)
        
    def start(self, source, sink):
        while True:
            if source.value == True: sink.perform()
            time.sleep(self.delay or source.delay)

class StartMonitor(Monitor):
    def __init__(self, config):
        super().__init__(config)
        
    def start(self, source, sink):
        sink.perform(state=source.value)
