import time
import subprocess
from actuator import log, util
from actuator.components import operator
from actuator.components.decorators import parameter, argument, input, output

ROLE_SOURCE = "source"


def instructions():
    return {
        'counter': CounterSource,
        'str': StringSource,
        'int': IntegerSource,
        'real': RealSource,
        'bool': BooleanSource,
        'value': ValueSource,
        'inflows': FlowSource,
        'none': NoneSource,
    }

def build(instruction, kwargs):
    return instructions()[instruction](kwargs)
        
    
#interface
class Source(operator.Operator):
    def set_upstream(self, upstream):
        raise Exception("Source cannot have an upstream operator")

    def wire(self, inflows):
        pass

    #return a boolean
    @property
    def value(self):
        raise Exception("Unimplemented for {}".format(self.kind))
    
    #Identifies this component as part of a flow
    @property
    def role(self): return ROLE_SOURCE
    


#Simple Source that takes a function and params
class FnSource(Source):
    def initialise(self, *args, **kwargs):
        super().initialise(*args, **kwargs)
        self._fn = kwargs['fn']
        self._parameters = kwargs['args']
    
    #return a boolean
    @property
    def value(self):
        return self._fn(**self._parameters)


class DelegatingSource(Source):
    def initialise(self, *args, **kwargs):
        super().initialise(*args, **kwargs)
        self._inner = kwargs.get('inner', None)

    @property
    def inner(self):
        return self._inner

    @property
    def kind(self):
        return "{}|{}".format(self.inner.kind, super().kind)



class FlowSource(Source):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._inflows = []
        self._named = util.parse_bool(kwargs.get('named', False))
        
    def initialise(self, *args, **kwargs):
        super().initialise(*args, **kwargs)
        
    
    def wire(self, inflows):
        self._inflows = inflows
    
    @property
    def inflows(self):
        return self._inflows
    
    @property
    def value(self):
        #no inflows, return None
        if len(self.inflows) == 0: return None
        #one inflow, return the payload
        if len(self.inflows) == 1: return self.inflows[0].get_payload()
        #more than one inflow, return a list of payloads
        if self._named:
            return {i.context.name: i.get_payload() for i in self.inflows}
        else:
            return [i.get_payload() for i in self.inflows]
            
    @property
    def description_data(self):
        d = super().description_data
        d[self.kind]["source-inflows"] = [{"name": i.name, "kind": i.kind} for i in self.inflows]
        return d

@argument('value', 'any', None, desc='Value to emit')
@output('any', 'Value provided as argument')
class ValueSource(Source):
    """
    Emits the given value
    """        
    @property
    def value(self):
        return self.args.value
    
@argument('value', 'str', "", desc='String value to emit')
@output('str', 'Value provided as argument')
class StringSource(Source):
    """
    Emits the given value, coerced to a string 
    """        
    @property
    def value(self):
        return str(self.args.value)


@argument('value', 'int', 0, desc='Integer value to emit')
@output('int', 'Value provided as argument')
class IntegerSource(Source):
    """
    Emits the given value, coerced to an integer
    """        
    @property
    def value(self):
        return int(self.args.value)

@argument('value', 'real', 0.0, desc='Real value to emit')
@output('real', 'Value provided as argument')
class RealSource(Source):
    """
    Emits the given value, coerced to a real (float)
    """
    @property
    def value(self):
        return float(self.args.value)

@argument('value', 'bool', False, desc='Boolean value to emit')
@output('bool', 'Value provided as argument')
class BooleanSource(Source):
    """
    Emits the given value, coerced to a boolean
    """
    @property
    def value(self):
        return util.parse_bool(self.args.value)



@parameter('start', 'int, real', 1, desc='Value to start counting at')
@parameter('increment', 'int, real', 1, desc='Amount by which to increment')
@output('int, real', 'Current counter value')
class CounterSource(Source):
    """
    Emits a number, incrementing the value each time it fires.
    """
    def initialise(self, *args, **kwargs):
        self._counter = self.params.start
        
    @property
    def value(self):
        value = self._counter
        self._counter += self.params.increment
        return value

@output('none', 'None')
class NoneSource(Source):
    """
    Emits None (null)
    """
    @property
    def value(self):
        return None

