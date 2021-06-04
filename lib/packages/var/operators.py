from actuator.components.operator import Operator, SinkOperator
from actuator import log, util
from . import sinks

class Set(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__(sinks.Set(*args, **kwargs))
        
        
