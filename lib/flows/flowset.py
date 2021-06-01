from actuator.flows.flow import FlowContext
from actuator.flows.scope import NamespacedScope

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
