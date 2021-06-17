from actuator.components.sink import Sink
from actuator import log, util

class Set(Sink):
    def initialise(self, *args, **kwargs):
        super().initialise(*args, **kwargs)
        self._varname = args[0]
        self._claimed = False

    def perform(self, payload):
        scope = self.context.scope
        scope.set(self._varname, payload, claim=(not self._claimed))
        self._claimed = True
        
        
