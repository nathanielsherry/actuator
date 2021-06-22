from actuator.flows.flow import Flow
from actuator.lang import parser
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
            self._source = parser.parse_source(s)
        return self

    def to(self, s):
        if isinstance(s, Sink):
            self._sink = s
        else:
            self._sink = parser.parse_sink(s)
        return self
        
    def on(self, s):
        if isinstance(s, Monitor):
            self._monitor = s
        else:
            self._monitor = parser.parse_monitor(s)
        return self
        
    def via(self, s):
        if isinstance(s, Operator):
            self._operator = s
        else:
            self._operator = parser.parse_operator(s)
        return self
        
    def flow(self, s):
        self._name = parser.parse_name(s)
        return self
        
    def build(self):            
        return Flow(
            self._source, 
            self._sink, 
            self._operator, 
            self._monitor, 
            self._name)
