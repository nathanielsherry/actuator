from actuator import util, component
from actuator.flows.scope import NamespacedScope
import threading


class FlowContext(component.Component):
    def __init__(self):
        super().__init__({})
        self._scope = None
    
    #To be called after `set_context`. If the former is about making
    #sure each component is aware of its relationships, then `wire` is
    #about using that information to make connections 
    def wire(self): raise Exception("Unimplemented")
    
    @property
    def scope(self): return self._scope
    

class Flow(FlowContext):
    def __init__(self, source, sink, operator, monitor, flowname):
        super().__init__()
        self._operator = operator
        self._source = source
        self._sink = sink
        self._monitor = monitor
        self._flowname = flowname
        
        #Threading is done w/ a callable back into this object
        self._thread = None

    def set_context(self, context):
        super().set_context(context)
        self._scope = NamespacedScope(context.scope)
        
        #Set this flow as the context for these components. This
        #is the earliest we can call this and still allow the 
        #components to access not just the Flow but also the FlowSet
        for c in self.components:
            c.set_context(self)

    def wire(self):
        from actuator import sink as mod_sink
        #Look up all of the sinks which are pointed at this flow and
        #feed it to the operator
        inbound = []
        for flow in self.context.flows:
            sink = flow.sink
            if not isinstance(sink, mod_sink.FlowSink): continue
            if not self.flowname == sink.target_name: continue
            inbound.append(flow)
        self.source.wire(inbound)
                
        #Wire the operators to the source
        self.operator.upstreams[0].set_upstream(self.source)        

    def start(self):
        self._thread = threading.Thread(target=lambda: self.run())
        self._thread.start()
        
    def join(self):
        self._thread.join()
        
    def run(self):
        self.monitor.start()
    
    
    @property
    def sink(self): return self._sink
    
    @property
    def source(self): return self._source
    
    @property
    def monitor(self): return self._monitor
    
    @property
    def operator(self): return self._operator
    
    @property
    def name(self): 
        return "{}:{}".format(super().name, self.flowname)
    
    @property
    def flowname(self):
        return self._flowname
    
    @property
    def components(self):
        cs = [] 
        cs.extend(self.operator.upstreams)
        cs.append(self.monitor)
        cs.append(self.sink)
        if cs[0] != self.source:
            cs = [self.source] + cs
        return cs
            
    @property
    def scope(self): return self._scope
    
    @property
    def description_data(self):
        data = {self.name: {
            'source': self.source.description_data,
            'operator': self.operator.description_data,
            'sink': self.sink.description_data,
            'monitor': self.monitor.description_data
        }}
        return data
    
        

    

class FlowSet(FlowContext):
    def __init__(self, flows):
        super().__init__()
        self._scope = NamespacedScope(None)
        self._flows = flows
        for flow in self.flows:
            flow.set_context(self)
            if flow.flowname:
                self._scope.set(flow.flowname, flow.scope)
        for flow in self.flows:
            flow.wire()
                
    @property
    def flows(self): return self._flows
    
    def start(self):
        for flow in self.flows:
            flow.start()
        for flow in self.flows:
            flow.join()
    
    @property
    def description_data(self):
        return {self.name: [n.description_data for n in self.flows]}
