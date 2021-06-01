import subprocess
import psutil
from actuator.components import source
from actuator import util

class Info(source.Source):
    def __init__(self, config):
        super().__init__(config)
        self._full = util.parse_bool(config.get('full', 'false'))
        self._keys = config.get('args', [])
        
    @property
    def value(self):
        if self._full:
            keys = list(psutil.Process().as_dict().keys())
        else:
            keys = ['pid', 'name', 'username', 'cmdline', 'cpu_percent', 'uids', 'gids', 'nice', 'status', 'cwd']
            if self._keys: keys.extend(self._keys)
            keys = list(set(keys))
        processes = []
        for proc in psutil.process_iter(keys):
            processes.append(proc.as_dict(attrs=keys))
        return processes



class Get(Info):
    def __init__(self, config):
        super().__init__(config)
        self._key = config.get['args'][0]
        
    @property
    def value(self):
        value = super().value
        return [p[self._key] for p in value]        

class Names(Info):
    def __init__(self, config):
        super().__init__(config)
        
    @property
    def value(self):
        value = super().value
        return [p['name'] for p in value]
    
class Has(source.Source):
    def __init__(self, config):
        super().__init__(config)
        self._search = config
    
    def compare(self, proc):
        keys = list(self._search.keys())
        d = proc.as_dict(attrs=keys)
        for key in keys:
            if d[key] != self._search[key]:
                return False
        return True
    
    @property
    def value(self):
        processes = []
        keys = list(self._search.keys())
        if len(keys) == 0: return False
        procs = psutil.process_iter(keys)
        for proc in procs:
            if self.compare(proc): return True
        return False
                            
