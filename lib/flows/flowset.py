from actuator.flows.flow import FlowContext
from actuator.flows.scope import NamespacedScope
import threading, time

class FlowSet(FlowContext):
    def __init__(self, flows):
        super().__init__()
        self._scope = NamespacedScope(None, self)
        self._flows = flows
                
    @property
    def flows(self): return self._flows
    
    def get_flow(self, name):
        for flow in self.flows:
            if flow.name == name:
                return flow
        return None
    
    def setup(self, delay=0):
        for flow in self.flows:
            flow.set_context(self)
            if delay: time.sleep(delay)
        for flow in self.flows:
            flow.wire()
            if delay: time.sleep(delay)
    
    def start(self, delay=0):
        self._thread = threading.Thread(target=lambda: self.run(delay), daemon=True)
        self._thread.start()
    
    def run(self, delay=0):
        try:
            for flow in self.flows:
                flow.start()
                if delay: time.sleep(delay)
            for flow in self.flows:
                flow.startup_wait()
                if delay: time.sleep(delay)
            self._started.set()
            for flow in self.flows:
                flow.join()
                if delay: time.sleep(delay)
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
        return {self.kind: [n.description_data for n in self.flows]}
