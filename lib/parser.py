from actuator import util
from actuator.package import REGISTRY

INSTRUCTION_SEPARATOR = '::'
PARAM_SEPARATOR = ','

KW_SINK = "to"
KW_MONITOR = "on"
KW_SOURCE = "from"
KW_OPERATOR = "via"
KEYWORDS = [KW_SINK, KW_MONITOR, KW_SOURCE, KW_OPERATOR]

PKG_SEP = '.' 

def twosplit(s, delim):
    parts = s.split(delim, maxsplit=1)
    first = parts[0]
    second = ""
    if len(parts) > 1:
        second = parts[1]
    return first, second


from actuator.flexer import FlexParser, SequenceParserMixin, PrimitivesParserMixin

#A Sequence PARSER for reading values or sequences of values
class ActuatorExpressionMixin:
    def __init__(self):
        if not '`' in self.flexer.lexer.quotes: self.flexer.lexer.quotes += '`'
        self._add_token_hook("act.source", lambda t: t == KW_SOURCE, lambda: self.parse_source())
        self._add_token_hook("act.sink", lambda t: t == KW_SINK, lambda: self.parse_sink())
        self._add_token_hook("act.monitor", lambda t: t == KW_MONITOR, lambda: self.parse_monitor())
        self._add_token_hook("act.operator", lambda t: t == KW_OPERATOR, lambda: self.parse_operator())
        
        #self.add_instruction_hooks(REGISTRY.source_names)
        #self.add_instruction_hooks(REGISTRY.sink_names)
        #self.add_instruction_hooks(REGISTRY.monitor_names)
        
    def add_instruction_hooks(self, instructions):
        for instruction in instructions:
            self.add_instruction_hook(instruction)
    
    #This needs to be a separate function from add_instruction_hooks to 
    #complete the closure in the test fn
    def add_instruction_hook(self, instruction):
            try:
                self._add_value_hook(
                    "act.inst.{}".format(instruction), 
                    lambda t: t == instruction,
                    lambda: self.flexer.pop(instruction)
                )
            except:
                pass
    
    def parse_instruction(self, key, valid_instruction, build, allow_upstream=False, upstream=None):
        from actuator.flexer import Symbol
        if key: key = self.flexer.pop(key)
        
        args = None
        kwargs = None
        #custom parsing for inline shell commands
        if self.flexer.peek().startswith('`'):
            args = [self.flexer.pop()[1:-1]]
            instruction = "sh"
        else:
            instruction = self.parse_packagename()
            if not valid_instruction(instruction):
                raise Exception("Invalid: '{}'".format(instruction))

            while True:
                if self.flexer.peek() == '[':
                    args = self.parse_list()
                    continue
                if self.flexer.peek() == '(':
                    kwargs = self.parse_keyvalue()
                    for key in kwargs.keys():
                        value = kwargs[key]
                        if isinstance(value, Symbol):
                            kwargs[key] = value.name
                    continue
                break
            
        if not kwargs: 
            kwargs = {}
            
        if args:
            kwargs['args'] = args
            
        finished = build(instruction, kwargs)
        
        if upstream:
            finished.set_upstream(upstream)
        
        if self.flexer.pop_if('|') == '|':
            if allow_upstream:
                return self.parse_instruction(None, valid_instruction, build, upstream=finished, allow_upstream=allow_upstream)
            else:
                raise Exception("Chaining this type of operator is not permitted")
        else:
            return finished

    
    def parse_packagename(self):
        topname = self.parse_value().name
        if self.flexer.pop_if('.') == PKG_SEP:
            subname = self.parse_value().name
            return topname + PKG_SEP + subname
        else:
            return topname

    #Parses a list of items.
    def parse_source(self):
        source = self.parse_instruction(KW_SOURCE, lambda t: t in REGISTRY.source_names, REGISTRY.build_source)
        return ('source', source)
    
    def parse_sink(self):
        sink = self.parse_instruction(KW_SINK, lambda t: t in REGISTRY.sink_names, REGISTRY.build_sink)
        return ('sink', sink)
    
    def parse_monitor(self):
        monitor = self.parse_instruction(KW_MONITOR, lambda t: t in REGISTRY.monitor_names, REGISTRY.build_monitor)
        return ('monitor', monitor)
        
    def parse_operator(self):
        operator = self.parse_instruction(KW_OPERATOR, lambda t: t in REGISTRY.operator_names, REGISTRY.build_operator, allow_upstream=True)
        return ('operator', operator)
        
        
        
        
        

class ActuatorParser(FlexParser, SequenceParserMixin, PrimitivesParserMixin, ActuatorExpressionMixin):
    def __init__(self, exp):
        super().__init__(exp)
        


def parse_actuator_expression_shell(args, default_source=None, default_sink=None):
    return parse_actuator_expression(" ".join(args), default_source, default_sink)

def parse_actuator_expression(exp, default_source=None, default_sink=None): 
    from actuator import source as mod_source
    from actuator import sink as mod_sink
    from actuator import monitor as mod_monitor
    from actuator import operator as mod_operator

    f = ActuatorParser(exp)
    parts = f.parse()
    result = {'expression': exp}
    for part in parts:
        result[part[0]] = part[1]
        
        #if isinstance(part, mod_source.Source):
        #    if 'source' in result:
        #        raise Exception("Found more than one source")
        #    result['source'] = part
        #elif isinstance(part, mod_sink.Sink):
        #    if 'sink' in result:
        #        raise Exception("Found more than one sink")
        #    result['sink'] = part
        #elif isinstance(part, mod_monitor.Monitor):
        #    if 'monitor' in result:
        #        raise Exception("Found more than one monitor")
        #    result['monitor'] = part
        #else:
        #    raise Exception("Found unrecognised component")

    #Create defaults if they were not included
    if not 'source' in result:
        result['source'] = default_source or REGISTRY.build_source('sh.stdin', {'split': 'false'})
    
    if not 'operator' in result:
        result['operator'] = REGISTRY.build_operator('noop', {})
        
    if not 'sink' in result:
        result['sink'] = default_sink or REGISTRY.build_sink('sh.stdout', {}) 
    
    if not 'monitor' in result:
        #First see if the sink has a preferred monitor
        sinkmon = result['sink'].custom_monitor()
        if sinkmon:
            result['monitor'] = sinkmon
        else:
            result['monitor'] = REGISTRY.build_monitor('start', {})
    
    #Connect the most upstream operator to the source
    result['operator'].upstreams[0].set_upstream(result['source'])
    
    #start_source = result['source']
    #while start_source.upstream:
    #    if default_source and not default_source.upstream:
    #        start_source._upstream = default_source
    #    else:
    #        start_source._upstream = REGISTRY.build_source('sh.stdin', {'split': 'false'})
    #    start_source = start_source.upstream
    
    

            

        

    
    return result
    
def parse_act_expression(exp):
    if not exp: return None
    f = ActuatorParser(exp)
    def valid(name):
        if name in REGISTRY.sink_names: return True
        if name in REGISTRY.source_names: return True
        return False
    def build(name, config):
        if name in REGISTRY.sink_names: return REGISTRY.build_sink(name, config)
        if name in REGISTRY.source_names: return REGISTRY.build_source(name, config)
        return None
    return f.parse_instruction(None, valid, build)
