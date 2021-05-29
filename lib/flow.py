from actuator import util, component
from actuator.scope import NamespacedScope
import threading


class FlowContext(component.Component):
    def __init__(self):
        super().__init__({})
        self._scope = NamespacedScope(None)       
    
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
        self._scope = None
        
        #Threading is done w/ a callable back into this object
        self._thread = None

        self._operator.upstreams[0].set_upstream(self._source)
        
        #Set this flow as the context for these components
        for c in self.components:
            c.set_context(self)

    def start(self):
        self._thread = threading.Thread(target=lambda: self.run())
        self._thread.start()
        
    def join(self):
        self._thread.join()
        
    def run(self):
        self._monitor.start(self._operator, self._sink)
    
    @property
    def name(self): 
        return "{}:{}".format(super().name, self.flowname)
    
    @property
    def flowname(self):
        return self._flowname
    
    @property
    def components(self):
        cs = [] 
        cs.extend(self._operator.upstreams)
        cs.append(self._monitor)
        cs.append(self._sink)
        return cs
            
    @property
    def scope(self): return self._scope
    
    @property
    def description_data(self):
        data = {self.name: {
            'source': self._source.description_data,
            'operator': self._operator.description_data,
            'sink': self._sink.description_data,
            'monitor': self._monitor.description_data
        }}
        return data
    
        

    

class FlowSet(FlowContext):
    def __init__(self, flows):
        super().__init__()
        self._flows = flows
        for flow in self.flows:
            flow.set_context(self)
            flow._scope = NamespacedScope(self.scope)
            if flow.flowname:
                self._scope.set(flow.flowname, flow.scope)
                
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
