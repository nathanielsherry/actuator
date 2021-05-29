from actuator.sink import Sink
from actuator import log, util

class Set(Sink):
    def __init__(self, config):
        super().__init__(config)
        self._varname = config.get('args', [''])[0]
        self._claimed = False

    def perform(self, payload):
        scope = self.context.scope
        scope.set(self._varname, payload, claim=(not self._claimed))
        self._claimed = True
        
        
