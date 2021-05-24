from actuator import source, util

class ToJson(source.DelegatingSource):
    def __init__(self, config):
        super().__init__(config)
        self._pretty = util.parse_bool(config.get('pretty', 'true'))
    
    @property
    def value(self):
        import json
        if self._pretty:
            return json.dumps(self.inner.value, indent=4)
        else:
            return json.dumps(self.inner.value)


class FromJson(source.DelegatingSource):
    def __init__(self, config):
        super().__init__(config)
    
    @property
    def value(self):
        import json
        value = json.loads(self.inner.value)
        return value
        
        
        
class ToYaml(source.DelegatingSource):
    def __init__(self, config):
        super().__init__(config)
        self._pretty = util.parse_bool(config.get('pretty', 'true'))
    
    @property
    def value(self):
        print("ASDF", flush=True)
        import yaml
        if self._pretty:
            return yaml.dump(self.inner.value)
        else:
            return yaml.dump(self.inner.value)


class FromYaml(source.DelegatingSource):
    def __init__(self, config):
        super().__init__(config)
    
    @property
    def value(self):
        import yaml
        return yaml.load(self.inner.value)
