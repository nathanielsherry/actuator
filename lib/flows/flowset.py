from actuator.flows.flow import FlowContext
from actuator.flows.scope import NamespacedScope
import threading

class FlowSet(FlowContext):
    def __init__(self, flows):
        super().__init__()
        self._scope = NamespacedScope(None, self)
        self._flows = flows
                
    @property
    def flows(self): return self._flows
    
    def get_flow(self, name):
        for flow in self.flows:
            if flow.flowname == name: 
                return flow
        return None
    
    def setup(self):
        for flow in self.flows:
            flow.set_context(self)
        for flow in self.flows:
            flow.wire()
    
    def start(self):
        self._thread = threading.Thread(target=lambda: self.run(), daemon=True)
        self._thread.start()
    
    def run(self):
        try:
            for flow in self.flows:
                flow.start()
            for flow in self.flows:
                flow.startup_wait()
            self._started.set()
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
