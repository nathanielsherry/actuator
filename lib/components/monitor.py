#!/usr/bin/python3

import time
from actuator import log, util
from actuator.components import component, source as mod_source, sink as mod_sink


def instructions():
    return {
        "change": ChangeMonitor,
        "interval": IntervalMonitor,
        "start": OnceMonitor,
        "demand": OnDemandMonitor,
        "counter": CountMonitor,
        "call": OnCallMonitor,
    }
    

def build(instruction, kwargs):
    return instructions()[instruction](kwargs)



class Monitor(component.Component):
        
    def start(self):
        raise Exception("Unimplemented for {}".format(self.kind))
    
    def stop(self):
        raise Exception("Unimplemented for {}".format(self.kind))
    
    @property
    def source(self): return self.context.source
    
    @property
    def sink(self): return self.context.sink
    
    @property
    def operator(self): return self.context.operator

    @property
    def threaded(self):
        #In general, monitors require a thread to run their flow
        return True

    def suggest_source(self):
        return None
    def suggest_sink(self):
        return None
    
    
    

class MonitorSleepMixin(component.ComponentMixin):
    def initialise(self, *args, **kwargs):
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
    
class ExitOnNoneMixin(component.ComponentMixin):
    def initialise(self, *args, **kwargs):
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
    def start(self):
        self.sink.perform(self.operator.value)
    def stop(self):
        pass


#Just runs once and exits. Good starter Monitor.
class CountMonitor(Monitor):
    def initialise(self, *args, **kwargs):
        self._count = int(args[0])
        self._terminate = False
    def start(self):
        for i in range(0, self._count):
            if self._terminate: return
            self.sink.perform(self.operator.value)
    def stop(self):
        self._terminate = True

#The interval monitor runs repeatedly with a delay, optionally exiting on a 
#None or, also optionally, False
class IntervalMonitor(Monitor, MonitorSleepMixin, ExitOnNoneMixin):
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
    def start(self):
        log.info("Starting {kind} with test {source} and sink {sink}".format(kind=self.kind, source=self.operator, sink=self.sink))
        last_state = None
        new_state = None
        while True:
            new_state = self.operator.value
            if new_state != last_state:
                log.info("{kind} yields '{state}' ({result}), running sink.".format(kind=self.kind, result="changed" if new_state != last_state else "unchanged", state=util.short_string(new_state)))
                self.sink.perform(new_state)
                last_state = new_state
            if not self.sleep(): return
            
    def stop(self):
        self.stop_sleep()

#NOTE: This monitor is never created through the expression explicitly. Instead
#this monitor can be returned by a sink when no monitor is specified, effectively
#allowing the sink to override the default, not the user
class OnDemandMonitor(Monitor, MonitorSleepMixin):
    def start(self):
        #Call sink.perform once in case there's any one-time setup needed
        self.sink.perform(self.demand())
        #Block the monitor thread so long as there are sinks showing as active
        while self.active_sinks:
            if not self.sleep(): break
        #Done, sleep has been interrupted or all sinks are inactive
        
    def stop(self):
        self.stop_sleep()
        
    def demand(self):
        #Unlike most monitors, this monitor serves requests from elsewhere. This
        #means that, because we may not be the first flow started, we may 
        #receive requests before we're ready. We must block those requests until
        #we're started
        self.context.startup_wait()
        return self.operator.value
    
    @property
    def active_sinks(self):
        return [s for s in self.context.sinks if s.active]
    

class OnCallMonitor(Monitor):

    class OnCallSource(mod_source.Source):
        def __init__(self):
            super().__init__()
            self._value = None

        @property
        def value(self):
            return self._value

        def set_value(self, value): self._value = value

    class OnCallSink(mod_sink.Sink):
        def __init__(self):
            super().__init__()


    def set_context(self, context):
        super().set_context(context)
        if not isinstance(context.source, OnCallMonitor.OnCallSource):
            raise Exception("{kind} cannot be used with a defined source".format(kind=self.kind))
        if not isinstance(context.sink, OnCallMonitor.OnCallSink):
            raise Exception("{kind} cannot be used with a defined sink".format(kind=self.kind))


    @property
    def threaded(self): return False
    def start(self): return
    def stop(self): return

    def call(self, payload):
        self.source.set_value(payload)
        result = self.operator.value
        self.source.set_value(None)
        return result

    def suggest_source(self):
        return OnCallMonitor.OnCallSource()

    def suggest_sink(self):
        return OnCallMonitor.OnCallSink()
