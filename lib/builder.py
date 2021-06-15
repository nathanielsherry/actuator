from actuator.flows.flow import Flow
from actuator.lang.parser import ActuatorParser
from actuator.components.sink import Sink
from actuator.components.source import Source
from actuator.components.monitor import Monitor
from actuator.components.operator import Operator

class FlowBuilder:
    def __init__(self):
        self._operator = None
        self._source = None
        self._sink = None
        self._monitor = None
        self._name = None
        
    
    def frm(self, s):
        if isinstance(s, Source):
            self._source = s
        else:
            self._source = ActuatorParser(s).parse_source(inline=True)[1]
        return self

    def to(self, s):
        if isinstance(s, Sink):
            self._sink = s
        else:
            self._sink = ActuatorParser(s).parse_sink(inline=True)[1]
        return self
        
    def on(self, s):
        if isinstance(s, Monitor):
            self._monitor = s
        else:
            self._monitor = ActuatorParser(s).parse_monitor(inline=True)[1]
        return self
        
    def via(self, s):
        if isinstance(s, Operator):
            self._operator = s
        else:
            self._operator = ActuatorParser(s).parse_operator(inline=True)[1]
        return self
        
    def flow(self, s):
        self._name = s
        return self
        
    def build(self):            
        return Flow(
            self._source, 
            self._sink, 
            self._operator, 
            self._monitor, 
            self._name)
