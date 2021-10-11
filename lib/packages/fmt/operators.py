from actuator import util
from actuator.components import operator

from actuator.components.decorators import parameter, argument, input, output, allarguments, operator


@input('any', 'Any payload')
@output('str', 'JSON String')
@parameter('pretty', 'bool', False, 'Apply formatting to JSON output')
class ToJson(operator.Operator):
    @property
    def value(self):
        import json
        value = self.upstream.value
        if value == None: return None
        if self.params.pretty:
            return json.dumps(value, indent=4)
        else:
            return json.dumps(value)


@input('str', 'JSON String')
@output('any', 'Parsed payload')
class FromJson(operator.Operator):
    @property
    def value(self):
        import json
        value = self.upstream.value
        if value == None: return None
        value = json.loads(value)
        return value
        
        

@input('any', 'Any payload')
@output('str', 'YAML String')
@parameter('unsafe', 'bool', False, 'Use unsafe PyYAML Dumper')
@parameter('canonical', 'bool', False, 'Dump YAML in canonical format with explicit types')
@parameter('default_flow_style', 'bool', True, "PyYAML's 'default_flow_style' argument")
class ToYaml(operator.Operator):
    @property
    def value(self):
        import yaml
        value = self.upstream.value
        if value == None: return None
        if not self.params.unsafe:
            return yaml.safe_dump(value, canonical=self.params.canonical)
        else:
            return yaml.dump(value, canonical=self.params.canonical)

@input('str', 'YAML String')
@output('any', 'Any payload')
@parameter('unsafe', 'bool', False, 'Use unsafe PyYAML Dumper')
class FromYaml(operator.Operator):
    @property
    def value(self):
        import yaml
        value = self.upstream.value
        if value == None: return None
        if self.params.unsafe:
            return yaml.load(value)
        else:
            return yaml.safe_load(value)
