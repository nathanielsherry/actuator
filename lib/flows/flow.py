from actuator import util
from actuator.components import component
from actuator.flows.scope import NamespacedScope
import threading


class FlowContext(component.Component):
    def __init__(self):
        super().__init__()
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
        from actuator.naming import get_random_name
        self._flowname = flowname or get_random_name()
        
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
        
        #Components stash their args&kwargs until setup time
        for c in self.components:
            c.setup()
        
        #Wire all inflows to the source
        self.source.wire(self.inflows)
                
        #Wire the operators to the source
        self.operator.upstreams[0].set_upstream(self.source)        

    def start(self):
        self._thread = threading.Thread(target=lambda: self.run(), daemon=True)
        self._thread.start()
        
    def stop(self):
        self.monitor.stop()
        self.sink.stop()
        
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
    def outflows(self):
        from actuator.components import sink, operator
        outflows = []
        for c in self.components:
            if isinstance(c, sink.Sink):
                outflows.append(c)
            elif isinstance(c, operator.SinkOperator):
                outflows.append(c.sink)
        return outflows
    
    @property
    def inflows(self):
        from actuator.components.sink import FlowSink
        inbound = []
        def is_inflow(o):
            return isinstance(o, FlowSink) and o.target_name == self.flowname
        for flow in self.context.flows:
            inbound.extend([o for o in flow.outflows if is_inflow(o)])
        return inbound
    
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
    
        

    


