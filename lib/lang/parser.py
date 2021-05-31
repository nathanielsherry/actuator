from actuator import util, flow
from actuator.package import REGISTRY

SYM_SEP = ';'
SYM_VARSTART = '$'
SYM_VARSEP = '.'
SYM_OUTFLOW = '@'
KW_SINK = "to"
KW_MONITOR = "on"
KW_SOURCE = "from"
KW_OPERATOR = "via"
KW_FLOW = "flow"
KEYWORDS = [KW_SOURCE, KW_SINK, KW_MONITOR, KW_OPERATOR, KW_FLOW]

PKG_SEP = '.' 

def twosplit(s, delim):
    parts = s.split(delim, maxsplit=1)
    first = parts[0]
    second = ""
    if len(parts) > 1:
        second = parts[1]
    return first, second


from actuator.lang.flexer import FlexParser, SequenceParserMixin, PrimitivesParserMixin

#A Sequence PARSER for reading values or sequences of values
class ActuatorExpressionMixin:
    def __init__(self):
        if not '`' in self.flexer.lexer.quotes: self.flexer.lexer.quotes += '`'
        self._add_token_hook("act.source", lambda t: t == KW_SOURCE, lambda: self.parse_source())
        self._add_token_hook("act.sink", lambda t: t == KW_SINK, lambda: self.parse_sink())
        self._add_token_hook("act.monitor", lambda t: t == KW_MONITOR, lambda: self.parse_monitor())
        self._add_token_hook("act.operator", lambda t: t == KW_OPERATOR, lambda: self.parse_operator())
        self._add_token_hook("act.flow", lambda t: t == KW_FLOW, lambda: self.parse_flow())
        self._add_token_hook("act.expsep", lambda t: t == SYM_SEP, lambda: self.parse_expsep())

    
    def parse_instruction(self, key, valid_instruction, build, allow_upstream=False, upstream=None):
        from actuator.lang.flexer import Symbol
        if key: key = self.flexer.pop(key)
        
        parseargs = True
        args = None
        kwargs = None
        #custom parsing for inline shell commands
        if self.flexer.peek().startswith('`'):
            args = [self.flexer.pop()[1:-1]]
            instruction = "sh"
            parseargs = False
        elif self.flexer.peek() == SYM_VARSTART:
            args = [self.parse_var()]
            instruction = "var"
        elif self.flexer.peek() == SYM_OUTFLOW and key == KW_SINK:
            self.flexer.pop(SYM_OUTFLOW)
            instruction = "outflow"
            parseargs = False
            args = [self.flexer.pop()]
        else:
            instruction = self.parse_packagename()
            if not valid_instruction(instruction):
                raise Exception("Invalid: '{}'".format(instruction))
                
        if parseargs:
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
        return (KW_SOURCE, source)
    
    def parse_sink(self):
        sink = self.parse_instruction(KW_SINK, lambda t: t in REGISTRY.sink_names, REGISTRY.build_sink)
        return (KW_SINK, sink)
    
    def parse_monitor(self):
        monitor = self.parse_instruction(KW_MONITOR, lambda t: t in REGISTRY.monitor_names, REGISTRY.build_monitor)
        return (KW_MONITOR, monitor)
        
    def parse_operator(self):
        operator = self.parse_instruction(KW_OPERATOR, lambda t: t in REGISTRY.operator_names, REGISTRY.build_operator, allow_upstream=True)
        return (KW_OPERATOR, operator)
               
    def parse_flow(self):
        self.flexer.pop(KW_FLOW)
        name = self.flexer.pop()
        return (KW_FLOW, name)
        
    def parse_expsep(self):
        self.flexer.pop(SYM_SEP)
        return (SYM_SEP, None)
        
    def parse_var(self):
        self.flexer.pop(SYM_VARSTART)
        keys = []
        while True:
            keys.append(self.flexer.pop())
            if not self.flexer.pop_if(SYM_VARSEP) == SYM_VARSEP:
                break
        
        return ".".join(keys)
        
        
        
        
        
        

class ActuatorParser(FlexParser, SequenceParserMixin, PrimitivesParserMixin, ActuatorExpressionMixin):
    def __init__(self, exp):
        super().__init__(exp)
        


def parse_actuator_expression(exp, default_source=None, default_sink=None): 
    from actuator import source as mod_source
    from actuator import sink as mod_sink
    from actuator import monitor as mod_monitor
    from actuator import operator as mod_operator
    f = ActuatorParser(exp)
    parts = f.parse()
    flowset = makeflowset(parts)

    return flowset

def makeflowset(parts):
    data = {}
    flows = []
    for part in parts:
        key, value = part
        if key == SYM_SEP:
            if data: flows.append(makeflow(data))
            data = {}
            continue
        if key in KEYWORDS:
            data[key] = value
    if data: flows.append(makeflow(data))
    return flow.FlowSet(flows)
        

def makeflow(kv):
    operator = kv.get(KW_OPERATOR, REGISTRY.build_operator('noop', {}))
    sink = kv.get(KW_SINK, REGISTRY.build_sink('sh.stdout', {}) )
    source = kv.get(KW_SOURCE, REGISTRY.build_source('sh.stdin', {'split': 'false'}))
    name = kv.get(KW_FLOW, None)
    monitor = kv.get(KW_MONITOR, None)
    #First see if the sink has a preferred monitor, then pick a default
    if not monitor: monitor = sink.custom_monitor()
    if not monitor: monitor = REGISTRY.build_monitor('start', {})
    
    return flow.Flow(source, sink, operator, monitor, name)
    


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
