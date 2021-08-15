import time
import subprocess
from actuator import log, util
from actuator.components import operator
from actuator.components.decorators import parameter, argument

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
class ValueSource(Source):
    """
    Emits the given value
    """        
    @property
    def value(self):
        return self.args.value
    
@argument('value', 'str', "", desc='String value to emit')
class StringSource(Source):
    """
    Emits the given value, coerced to a string 
    """        
    @property
    def value(self):
        return str(self.args.value)


@argument('value', 'int', 0, desc='Integer value to emit')
class IntegerSource(Source):
    """
    Emits the given value, coerced to an integer
    """        
    @property
    def value(self):
        return int(self.args.value)

@argument('value', 'real', 0.0, desc='Real value to emit')
class RealSource(Source):
    """
    Emits the given value, coerced to a real (float)
    """
    @property
    def value(self):
        return float(self.args.value)

@argument('value', 'bool', False, desc='Boolean value to emit')
class BooleanSource(Source):
    """
    Emits the given value, coerced to a boolean
    """
    @property
    def value(self):
        return util.parse_bool(self.args.value)



@parameter('start', 'int', 1, desc='Value to start counting at')
@parameter('increment', 'int', 1, desc='Amount by which to increment')
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


class NoneSource(Source):
    @property
    def value(self):
        return None







class WeatherCanadaSource(Source):
    def initialise(self, *args, **kwargs):
        super().initialise(*args, **kwargs)
        self._province = kwargs['province']
        self._citycode = kwargs['citycode']
        self._current = kwargs.get('current', None)
        self._low = kwargs.get('low', None)
        self._high = kwargs.get('high', None)
        if self._current: self._current = float(self._current)
        if self._low: self._low = float(self._low)
        if self._high: self._high = float(self._high)
        
        log.info("{kind} received initial config {config}".format(kind=self.kind, config=(args, kwargs)))
    
    @property
    def value(self):
        from lxml import objectify
        xmlstring = util.get_url("https://dd.weather.gc.ca/citypage_weather/xml/{province}/s{citycode}_e.xml".format(province=self._province, citycode=self._citycode))
        root = objectify.fromstring(xmlstring.encode())
        current = root.currentConditions.temperature
        if root.forecastGroup.forecast[0].period.text.endswith('night'):
            #first entry is evening low followed by tomorrow's high.                             
            low = root.forecastGroup.forecast[0].temperatures.temperature
            high = root.forecastGroup.forecast[1].temperatures.temperature
        else:
            #first entry is daily high, followed by this evening's low
            high = root.forecastGroup.forecast[0].temperatures.temperature
            low = root.forecastGroup.forecast[1].temperatures.temperature
        
        log.info("{kind} received weather data: current={current}, high={high}, low={low}".format(kind=self.kind, current=current, low=low, high=high))
        
        if self._current != None:
            if self._current <= current: return False
        if self._low != None:
            if self._low <= low: return False
        if self._high != None:
            if self._high <= high: return False
            
        return True




