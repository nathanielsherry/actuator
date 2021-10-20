#!/usr/bin/python3

import time, traceback
from actuator import log, util
from actuator.components import component, source as mod_source, sink as mod_sink
from actuator.components.decorators import parameter, argument, input, output, allarguments

ROLE_MONITOR = "monitor"

def instructions():
    return {
        "change": ChangeMonitor,
        "interval": IntervalMonitor,
        "start": OnceMonitor,
        "demand": OnDemandMonitor,
        "counter": CountMonitor,
        "call": OnCallMonitor,
        "input": OnInputMonitor,
        "value": OnValueMonitor,
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
    
    #Identifies this component as part of a flow
    @property
    def role(self): return ROLE_MONITOR
    

@parameter('sleep', 'int', 1, 'Interval between activations')
class MonitorSleepMixin(component.Component):
    def initialise(self, *args, **kwargs):
        from threading import Event
        self._sleeper = Event()
        self._stopped = False
            
    def sleep(self):
        try:
            self._sleeper.wait(self.params.sleep)
        except:
            import traceback, sys
            sys.stderr.write(traceback.format_exc())
            return False
        return not self._stopped
        
        
    def stop_sleep(self):
        self._stopped = True
        self._sleeper.set()
    
@parameter('exit_on_none', 'bool', True, 'Exit if the monitor receives a None value from its source')
@parameter('exit_on_false', 'bool', False, 'Exit if the monitor receives a False value from its source')
@parameter('exit_on_emptystr', 'bool', False, 'Exit if the monitor receives a "" (empty string) value from its source')
class ExitOnValueMixin(component.Component):
    def value_is_exit_condition(self, value):
        if self.params.exit_on_none and value == None: return True
        if self.params.exit_on_false and value == False: return True
        if self.params.exit_on_emptystr and value == '': return True
        return False


#Just runs once and exits. Good starter Monitor.
class OnceMonitor(Monitor):
    def start(self):
        try:
            self.sink.perform(self.operator.value)
        except:
            raise
    def stop(self):
        pass


#Just runs n times and exits. Good starter Monitor.
class CountMonitor(Monitor):
    def initialise(self, *args, **kwargs):
        self._count = int(args[0])
        self._terminate = False
    def start(self):
        for i in range(0, self._count):
            try:
                if self._terminate: return
                self.sink.perform(self.operator.value)
            except:
                self.logger.error(traceback.format_exc())
                
    def stop(self):
        self._terminate = True


#Runs until terminated
class OnInputMonitor(Monitor):
    def initialise(self, *args, **kwargs):
        self._terminate = False
    def start(self):
        while True:
            try:
                if self._terminate: return
                self.sink.perform(self.operator.value)
            except:
                self.logger.error(traceback.format_exc())
    def stop(self):
        self._terminate = True


#The interval monitor runs repeatedly with a delay, optionally exiting on a 
#None or, also optionally, False
class IntervalMonitor(Monitor, MonitorSleepMixin, ExitOnValueMixin):
    def start(self):
        while True:
            try:
                #Get the value from the source
                value = self.operator.value
                            
                #if we exit on an exit condition value, and this is one, return
                if self.value_is_exit_condition(value):
                    return
                
                #Pass the value to the sink
                self.sink.perform(value)
            except:
                self.logger.error(traceback.format_exc())
            
            #sleep for the specified interval
            if not self.sleep(): return

    def stop(self):
        self.stop_sleep()


#Monitors the result of a Source over time, triggering an event (callback) 
#when the value changes, passing the new state as the single argument.
class ChangeMonitor(Monitor, MonitorSleepMixin):
    def start(self):
        self.logger.info("Starting with source %s and sink %s", self.operator, self.sink)
        last_state = None
        new_state = None
        while True:
            try:
                new_state = self.operator.value
                if new_state != last_state:
                    self.logger.info("State '%s' (%s), running sink", util.short_string(new_state), "changed" if new_state != last_state else "unchanged")
                    self.sink.perform(new_state)
                    last_state = new_state
            except:
                self.logger.error(traceback.format_exc())
                
            if not self.sleep(): return
            
    def stop(self):
        self.stop_sleep()


#Monitors the result of a Source over time, triggering an event (callback) 
#when the value matches (or changes to match) a given value. Passes the 
#matched state as the single argument.
@argument('value', 'any', None, 'Value for comparison')
@parameter('always', 'bool', False, 'Only fire on a state change')
class OnValueMonitor(Monitor, MonitorSleepMixin):
    def start(self):
        self.logger.info("Starting with source %s and sink %s", self.operator, self.sink)
        last_state = None
        new_state = None
        while True:
            try:
                changed = new_state != last_state
                new_state = self.operator.value
                if new_state == self.args.value and (changed or self.params.always):
                    self.logger.info("State '%s' (%s), running sink", util.short_string(new_state), "changed" if new_state != last_state else "unchanged")
                    self.sink.perform(new_state)
                    last_state = new_state
            except:
                self.logger.error(traceback.format_exc())
                
            if not self.sleep(): return
            
    def stop(self):
        self.stop_sleep()



#NOTE: This monitor is never created through the expression explicitly. Instead
#this monitor can be returned by a sink when no monitor is specified, effectively
#allowing the sink to override the default, not the user
class OnDemandMonitor(Monitor, MonitorSleepMixin):
    def start(self):
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
        try:
            return self.operator.value
        except:
            self.logger.error(traceback.format_exc())
    
    @property
    def active_sinks(self):
        return [s for s in self.context.sinks if s.active]
    
    
class OnCallMonitor(Monitor):

    class OnCallSource(mod_source.Source):
        def construct(self):
            self._value = None

        @property
        def value(self):
            return self._value

        def set_value(self, value): self._value = value

    class OnCallSink(mod_sink.Sink):
        pass

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
        try:
            self.source.set_value(payload)
            result = self.operator.value
            self.source.set_value(None)
            return result
        except:
            self.logger.error(traceback.format_exc())

    def suggest_source(self):
        return OnCallMonitor.OnCallSource()

    def suggest_sink(self):
        return OnCallMonitor.OnCallSink()
