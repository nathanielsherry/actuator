from actuator.source import Source
from actuator import log, util

class Get(Source):
    def __init__(self, config):
        super().__init__(config)
        self._varname = config.get('args', ['default'])[0]

    @property
    def value(self):
        scope = self.context.scope
        #TODO: pickle-copy?
        if not scope.has(self._varname):
            return None
        return scope.get(self._varname)
        
        
