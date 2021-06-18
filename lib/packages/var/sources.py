from actuator.components.source import Source
from actuator import log, util
import time

class Get(Source):
    def initialise(self, *args, **kwargs):
        super().initialise(*args, **kwargs)
        self._varname = args[0]
        self._wait = util.parse_bool(kwargs.get('wait', True))

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
        
        
