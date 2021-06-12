from actuator import util
from actuator.flows import flow
from actuator.flows import flowset
from actuator.package import REGISTRY

SYM_SEP = ';'
SYM_VARSTART = '$'
SYM_VARSEP = '.'
SYM_FLOWREF = '@'
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

        self._add_value_hook("act.variable", lambda t: t == SYM_VARSTART, lambda: self.parse_var())
        self._add_value_hook("act.flowref", lambda t: t == SYM_FLOWREF, lambda: self.parse_flowref())
    
    def parse_instruction(self, key, valid_instruction, build):
        from actuator.lang.flexer import Symbol
        if key: key = self.flexer.pop(key)
        
        parseargs = True
        args = None
        kwargs = None
        instruction = None
        #custom parsing for inline shell commands
        if self.flexer.peek().startswith('`'):
            args = [self.flexer.pop()[1:-1]]
            instruction = "sh"
            parseargs = False
        elif self.flexer.peek() == SYM_VARSTART:
            args = [self.parse_var().reference]
            instruction = "var"
            parseargs = False
        elif self.flexer.peek() == SYM_FLOWREF:
            args = [self.parse_flowref()]
            instruction = "_flowref"
            parseargs = False
        elif self.flexer.peek().startswith('"') or self.flexer.peek().startswith("'"):
            args = [self.flexer.pop()[1:-1]] 
            instruction = "str"
            parseargs = False
        else:
            instruction = self.parse_packagename()
            if not valid_instruction(instruction):
                raise Exception("Invalid: '{}'".format(instruction))
                
        if parseargs:
            if self.flexer.peek() == '(':
                args, kwargs = self.parse_args()

        if not kwargs: kwargs = {}
        if not args: args = []
        return build(instruction, *args, **kwargs)
    
        
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
    
    def parse_sink(self, inline=False):
        key = None if inline else KW_SINK
        sink = self.parse_instruction(key, lambda t: t in REGISTRY.sink_names, REGISTRY.build_sink)
        return (KW_SINK, sink)
    
    def parse_monitor(self):
        monitor = self.parse_instruction(KW_MONITOR, lambda t: t in REGISTRY.monitor_names, REGISTRY.build_monitor)
        return (KW_MONITOR, monitor)
        
    def parse_operator(self):
        self.flexer.pop(KW_OPERATOR)
        operator = self.parse_opchain()
        return (KW_OPERATOR, operator)
               
    def parse_opchain(self, upstream=None):
        CHAIN_OPS = ['|', '>']
        
        #No default chainop, if there's an upstream, we should parse one
        chainop = None
        if upstream:
            chainop = self.flexer.pop(*CHAIN_OPS)
        
        if not chainop or chainop == "|":
            #normal (or no) chaining, just parse the op
            operator = self.parse_instruction(None, lambda t: t in REGISTRY.operator_names, REGISTRY.build_operator)
        elif chainop == ">":
            #Sink chaining, parse as a sink and wrap in a SinkOperator
            from actuator.components.operator import SinkOperator
            sink = self.parse_sink(inline=True)
            operator = SinkOperator(sink[1])
        
        
        #If there was an operator before this one, set it
        if upstream:
            operator.set_upstream(upstream)
        
        #If there is an operator after this one, recurse to parse it
        if self.flexer.peek() in CHAIN_OPS:
            return self.parse_opchain(operator)
        else:
            return operator
               
               
    def parse_flow(self):
        self.flexer.pop(KW_FLOW)
        name = self.flexer.pop()
        return (KW_FLOW, name)

    def parse_flowref(self):
        self.flexer.pop(SYM_FLOWREF)
        name = self.flexer.pop()
        return FlowReference(name)

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
        
        return VariableReference(".".join(keys))
        
        
        
        

class Reference:
    def __init__(self, reference):
        self._reference = reference
        
    @property
    def reference(self): return self._reference

    def dereference(self, flowctx):
        raise Exception("Unimplemented")

class VariableReference(Reference):
    def dereference(self, flowctx):
        return flowctx.scope.get(self.reference)
    
class FlowReference(Reference):
    def dereference(self, flowctx):
        return flowctx.get_flow(self.reference)




class ActuatorParser(FlexParser, SequenceParserMixin, PrimitivesParserMixin, ActuatorExpressionMixin):
    def __init__(self, exp):
        super().__init__(exp)
        


def parse_actuator_expression(exp, default_source=None, default_sink=None): 
    from actuator.components import source as mod_source
    from actuator.components import sink as mod_sink
    from actuator.components import monitor as mod_monitor
    from actuator.components import operator as mod_operator
    
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
    return flowset.FlowSet(flows)
        

def makeflow(kv):
    operator = kv.get(KW_OPERATOR, REGISTRY.build_operator('noop', {}))
    sink = kv.get(KW_SINK, None)
    source = kv.get(KW_SOURCE, None)
    name = kv.get(KW_FLOW, None)
    monitor = kv.get(KW_MONITOR, None)

    #If a monitor has been defined but source/sink hasn't, give the monitor
    #a chance to make a suggestion
    if not source and monitor: source = monitor.suggest_source()
    if not sink and monitor: sink = monitor.suggest_sink()

    #If the monitor declines, fall back to defaults for shell
    if not sink: sink = REGISTRY.build_sink('sh.stdout', {})
    if not source: source = REGISTRY.build_source('sh.stdin', {'split': 'false'})

    #If the *monitor* wasn't defined, see if the sink has a preferred monitor,
    #then pick a default
    if not monitor: monitor = sink.suggest_monitor()
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
