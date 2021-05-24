from actuator import operator, util

class ToJson(operator.Operator):
    def __init__(self, config):
        super().__init__(config)
        self._pretty = util.parse_bool(config.get('pretty', 'true'))
    
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
    def __init__(self, config):
        super().__init__(config)
    
    @property
    def value(self):
        import json
        value = self.upstream.value
        if value == None: return None
        value = json.loads(value)
        return value
        
        
        
class ToYaml(operator.Operator):
    def __init__(self, config):
        super().__init__(config)
        self._pretty = util.parse_bool(config.get('pretty', 'true'))
    
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
    def __init__(self, config):
        super().__init__(config)
    
    @property
    def value(self):
        import yaml
        value = self.upstream.value
        if value == None: return None
        return yaml.load(value)
