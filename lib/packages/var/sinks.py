from actuator.sink import Sink
from actuator import log, util

class Set(Sink):
    def __init__(self, config):
        super().__init__(config)
        self._varname = config.get('args', [''])[0]
        self._claimed = False

    def claim(self):
        if self._claimed: return
        scope = self.context.scope
        if not scope.claim(self._varname):
            raise Exception("Variable '{}' already claimed".format(self._varname))
        self._claimed = True

    def perform(self, payload):
        self.claim()
        scope = self.context.scope
        scope.set(self._varname, payload)
        
        
