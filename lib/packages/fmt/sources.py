from actuator import source, util

class ToJson(source.DelegatingSource):
    def __init__(self, config):
        super().__init__(config)
        self._pretty = util.parse_bool(config.get('pretty', 'true'))
    
    @property
    def value(self):
        import json
        value = self.inner.value
        if value == None: return None
        if self._pretty:
            return json.dumps(value, indent=4)
        else:
            return json.dumps(value)


class FromJson(source.DelegatingSource):
    def __init__(self, config):
        super().__init__(config)
    
    @property
    def value(self):
        import json
        value = self.inner.value
        if value == None: return None
        value = json.loads(value)
        return value
        
        
        
class ToYaml(source.DelegatingSource):
    def __init__(self, config):
        super().__init__(config)
        self._pretty = util.parse_bool(config.get('pretty', 'true'))
    
    @property
    def value(self):
        import yaml
        value = self.inner.value
        if value == None: return None
        if self._pretty:
            return yaml.dump(value)
        else:
            return yaml.dump(value)


class FromYaml(source.DelegatingSource):
    def __init__(self, config):
        super().__init__(config)
    
    @property
    def value(self):
        import yaml
        value = self.inner.value
        if value == None: return None
        return yaml.load(value)
