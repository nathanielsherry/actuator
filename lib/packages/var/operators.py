from actuator.operator import Operator, SinkOperator
from actuator import log, util
from . import sinks

class Set(Operator):
    def __init__(self, config):
        super().__init__(sinks.Set(config))
        
        
