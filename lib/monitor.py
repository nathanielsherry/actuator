#!/usr/bin/python3

import time
from actuator import log, util


def instructions():
    return {
        "change": ChangeMonitor,
        "interval": IntervalMonitor,
        "start": OnceMonitor,
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
        

class MonitorSleepMixin:
    def __init__(self, config):
        self._sleep = float(config.get('sleep', '1'))
            
    def sleep(self):
        import time
        time.sleep(self._sleep)
    
class ExitOnNoneMixin:
    def __init__(self, config):
        self._exit_on_none = util.parse_bool(config.get('exit', 'true'))
        self._bool = util.parse_bool(config.get('bool', 'true'))
        self._blank = util.parse_bool(config.get('blank', 'true'))
            
    @property
    def exit_on_none(self): 
        return self._exit_on_none
    
    def value_is_none(self, value):
        if value == None: return True
        if self._bool and value == False: return True
        if self._blank and value == '': return True
        return False


#Just runs once and exits. Good starter Monitor.
class OnceMonitor(Monitor):
    def __init__(self, config):
        super().__init__(config)
        
    def start(self, source, sink):
        sink.perform(source.value)



#The interval monitor runs repeatedly with a delay, optionally exiting on a 
#None or, also optionally, False
class IntervalMonitor(Monitor, MonitorSleepMixin, ExitOnNoneMixin):
    def __init__(self, config):
        super().__init__(config)
    
    def start(self, source, sink):
        while True:
            #Get the value from the source
            value = source.value
                        
            #if we exit on a None value, and this is one, return
            if self.value_is_none(value) and self.exit_on_none:
                return
            
            #Pass the value to the sink
            sink.perform(value)
            
            #sleep for the specified interval
            self.sleep()

            


#Monitors the result of a Source over time, triggering an event (callback) 
#when the value changes, passing the new state as the single argument.
class ChangeMonitor(Monitor, MonitorSleepMixin):
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
                sink.perform(new_state)
                last_state = new_state
            self.sleep()

#NOTE: This monitor is never created through the expression explicitly. Instead
#this monitor can be returned by a sink when no monitor is specified, effectively
#allowing the sink to override the default, not the user
class OnDemandMonitor(Monitor):
    def __init__(self, config):
        super().__init__(config)
        
        
    def start(self, source, sink):
        self._source = source
        self._sink = sink
        #Call sink.perform once in case there's any one-time setup needed
        self._sink.perform(self.demand())
        #Block the monitor thread as if we were doing something important
        import time
        while True: time.sleep(1)
        
    def demand(self):
        return self._source.value
        




