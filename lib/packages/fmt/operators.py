from actuator import util
from actuator.components import operator

class ToJson(operator.Operator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pretty = util.parse_bool(kwargs.get('pretty', 'true'))
    
    @property
    def value(self):
        import json
        value = self.upstream.value
        if value == None: return None
        if self._pretty:
            return json.dumps(value, indent=4)
        else:
            return json.dumps(value)


class FromJson(operator.Operator):
    @property
    def value(self):
        import json
        value = self.upstream.value
        if value == None: return None
        value = json.loads(value)
        return value
        
        
        
class ToYaml(operator.Operator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pretty = util.parse_bool(kwargs.get('pretty', 'true'))
    
    @property
    def value(self):
        import yaml
        value = self.upstream.value
        if value == None: return None
        if self._pretty:
            return yaml.dump(value)
        else:
            return yaml.dump(value)


class FromYaml(operator.Operator):
    @property
    def value(self):
        import yaml
        value = self.upstream.value
        if value == None: return None
        return yaml.load(value)
