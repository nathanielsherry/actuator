from actuator import operator, util

def tobool(o):
    if isinstance(o, bool): return o
    if isinstance(o, str): return util.parse_bool(o)
    #If it's not a bool or a string, fall back on python's truthy/falsey value
    if o:
        return True
    else:
        return False

class Not(operator.Operator):
    def __init__(self, config):
        super().__init__(config)
    
    @property
    def value(self):
        import json
        value = tobool(self.upstream.value)
        return not value
    
    
class Any(operator.Operator):
    def __init__(self, config):
        super().__init__(config)
    
    @property
    def value(self):
        import json
        value = self.upstream.value
        if not isinstance(value, (list, tuple)):
            value = list(value)
        return any(value)
        
class All(operator.Operator):
    def __init__(self, config):
        super().__init__(config)
    
    @property
    def value(self):
        import json
        value = self.upstream.value
        if not isinstance(value, (list, tuple)):
            value = list(value)
        return all(value)