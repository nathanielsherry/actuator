from actuator.flows.flow import FlowContext
from actuator.flows.scope import NamespacedScope

class FlowSet(FlowContext):
    def __init__(self, flows):
        super().__init__()
        self._scope = NamespacedScope(None)
        self._flows = flows
                
    @property
    def flows(self): return self._flows
    
    def setup(self):
        for flow in self.flows:
            flow.set_context(self)
        for flow in self.flows:
            flow.scope.set('global', self.scope, claim=True)
            if flow.flowname: self.scope.set(flow.flowname, flow.scope, claim=True)
        for flow in self.flows:
            flow.wire()
    
    def start(self):
        try:
            for flow in self.flows:
                flow.start()
            for flow in self.flows:
                flow.join()
        except KeyboardInterrupt:
            try:
                for flow in self.flows:
                    flow.stop()
            except:
                import traceback, sys
                sys.stderr.write(traceback.format_exc())
        except:
            import traceback, sys
            sys.stderr.write(traceback.format_exc())
        finally:
            for flow in self.flows:
                flow.join()
            

    @property
    def description_data(self):
        return {self.name: [n.description_data for n in self.flows]}
