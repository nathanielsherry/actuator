from actuator.source import Source
from actuator import log, util
import time

class Get(Source):
    def __init__(self, config):
        super().__init__(config)
        self._varname = config.get('args', [''])[0]
        self._wait = util.parse_bool(config.get('wait', True))

    @property
    def value(self):
        scope = self.context.scope
        #TODO: pickle-copy?
        while not scope.has(self._varname):
            if self._wait:
                time.sleep(1)
            else:
                return None
        return scope.get(self._varname)
        
        
