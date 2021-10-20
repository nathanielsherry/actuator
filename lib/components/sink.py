#!/usr/bin/python3

from actuator import log, util
from actuator.components import component


ROLE_SINK = "sink"



def instructions():
    return {
        "_flowref": FlowSink,
        "none": NoneSink,
    }
    
    
def build(instruction, kwargs):
    return instructions()[instruction](kwargs)    
    


class Sink(component.Component):
    def perform(self, payload):
        raise Exception("Unimplemented for {}".format(self.kind))
       
    @property
    def active(self):
        #by default, sinks are passive, accepting input as it arrives
        #sinks which are in control somehow should return True so long 
        #as they are active (ie not stopped/finished) 
        return False
    
    #There are cases where the sink may want to provide
    #its own monitor so that pull-based sink implementations
    #such as a web server may fetch data more effectively
    def suggest_monitor(self):
        return None

    #Identifies this component as part of a flow
    @property
    def role(self): return ROLE_SINK


class OnDemandMixin(component.ComponentMixin):
    def construct(self):
        self._monitor = None
    
    def initialise(self, *args, **kwargs):
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
        raise Exception("Unimplemented for {}".format(self.kind))

class RunnerSink(Sink):
    def perform(self, payload):
        self.run()
    def run(self):
        raise Exception("Unimplemented for {}".format(self.kind))


class FlowSink(Sink, OnDemandMixin):
    #Stash the target name early, so that once the context is set
    #we'll have everything we need to wire flows together
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._target_ref = args[0]
           
    #Once the context is set, we have everything we need to look up
    #The target flow. This allows us to wire earlier
    def set_context(self, context):
        super().set_context(context)
        flow = self.context
        flowset = flow.context
        self._target = self._target_ref.dereference(flowset)
        
    #Everything has already been done by __init__ and set_context
    def initialise(self, *args, **kwargs):
        super().initialise(*args, **kwargs)
        
    
    #This sink is active as long as it's target flow is running
    @property
    def active(self):
        from actuator.flows.flow import Flow 
        return self.target.state == Flow.STATE_STARTED
    
    @property
    def target_name(self): return self._target_ref.reference
    
    @property
    def target(self): return self._target
    
    def suggest_monitor(self):
        return self.ondemand_monitor
    
    def perform(self, payload):
        self.set_payload(payload)

    @property
    def description_data(self):
        d = super().description_data
        if self.target: 
            d[self.kind]["flowsink-target"] = {"name": self.target.name, "kind": self.target.kind}
        elif self.target_name:
            d[self.kind]["flowsink-targetname"] = self.target.name
        return d
        
        



import threading
class DedicatedThreadSink(Sink):
    def initialise(self, *args, **kwargs):
        super().initialise(*args, **kwargs)
        self._dedicated = None
        self._active = True
        
    @property
    def active(self): return self._active
    
    def start(self):
        self._dedicated = self.make_dedicated()
        self.dedicated.start()
    
    def perform(self, payload):
        self.set_dedicated_state(payload)

    @property
    def dedicated(self):
        return self._dedicated

    def stop_dedicated(self):
        self.dedicated.terminate()

    def stop(self):
        self.stop_dedicated()
        self._active = False

    def make_dedicated(self): raise Exception("Unimplemented")
    def set_dedicated_state(self, kwargs): raise Exception("Unimplemented")


class DedicatedThread(threading.Thread):
    def construct(self):
        self._terminated = threading.Event()
    
    #Called when the thread starts by the thread itself
    #the method should call self._terminated.set() at the end to signal
    #that it has completed
    def run(self): raise Exception("Unimplemented")
    
    #Called when the thread is asked to end, not by the thread itself.
    #Should call self._terminated.wait() 
    def terminate(self): raise Exception("Unimplemented")


class NoneSink(Sink):
    def perform(self, payload):
        pass




    
    


        

