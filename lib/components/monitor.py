#!/usr/bin/python3

import time
from actuator import log, util
from actuator.components import component


def instructions():
    return {
        "change": ChangeMonitor,
        "interval": IntervalMonitor,
        "start": OnceMonitor,
    }
    

def build(instruction, kwargs):
    return instructions()[instruction](kwargs)



class Monitor(component.Component):
        
    def start(self):
        raise Exception("Unimplemented")
    
    def stop(self):
        raise Exception("Unimplemented")
    
    @property
    def source(self): return self.context.source
    
    @property
    def sink(self): return self.context.sink
    
    @property
    def operator(self): return self.context.operator
    
    
    

class MonitorSleepMixin:
    def __init__(self, *args, **kwargs):
        from threading import Event
        self._sleep = float(kwargs.get('sleep', '1'))
        self._sleeper = Event()
        self._stopped = False
            
    def sleep(self):
        try:
            self._sleeper.wait(self._sleep)
        except:
            import traceback, sys
            sys.stderr.write(traceback.format_exc())
            return False
        return not self._stopped
        
        
    def stop_sleep(self):
        self._stopped = True
        self._sleeper.set()
    
class ExitOnNoneMixin:
    def __init__(self, *args, **kwargs):
        self._exit_on_none = util.parse_bool(kwargs.get('exit', 'true'))
        self._bool = util.parse_bool(kwargs.get('bool', 'false'))
        self._blank = util.parse_bool(kwargs.get('blank', 'false'))
            
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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def start(self):
        self.sink.perform(self.operator.value)



#The interval monitor runs repeatedly with a delay, optionally exiting on a 
#None or, also optionally, False
class IntervalMonitor(Monitor, MonitorSleepMixin, ExitOnNoneMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def start(self):
        while True:
            try:
                #Get the value from the source
                value = self.operator.value
                            
                #if we exit on a None value, and this is one, return
                if self.value_is_none(value) and self.exit_on_none:
                    return
                
                #Pass the value to the sink
                self.sink.perform(value)
            except:
                import traceback
                log.error(traceback.format_exc())
            
            #sleep for the specified interval
            if not self.sleep(): return

    def stop(self):
        self.stop_sleep()


#Monitors the result of a Source over time, triggering an event (callback) 
#when the value changes, passing the new state as the single argument.
class ChangeMonitor(Monitor, MonitorSleepMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def start(self):
        log.info("Starting {name} with test {source} and sink {sink}".format(name=self.name, source=self.operator, sink=self.sink))
        last_state = None
        new_state = None
        while True:
            new_state = self.operator.value
            if new_state != last_state:
                log.info("{name} yields '{state}' ({result}), running sink.".format(name=self.name, result="changed" if new_state != last_state else "unchanged", state=util.short_string(new_state)))
                self.sink.perform(new_state)
                last_state = new_state
            if not self.sleep(): return
            
    def stop(self):
        self.stop_sleep()

#NOTE: This monitor is never created through the expression explicitly. Instead
#this monitor can be returned by a sink when no monitor is specified, effectively
#allowing the sink to override the default, not the user
class OnDemandMonitor(Monitor, MonitorSleepMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        
    def start(self):
        #Call sink.perform once in case there's any one-time setup needed
        self.sink.perform(self.demand())
        #Block the monitor thread as if we were doing something important
        while True:
            if not self.sleep(): return
        
    def stop(self):
        self.stop_sleep()
        
    def demand(self):
        return self.operator.value
        




