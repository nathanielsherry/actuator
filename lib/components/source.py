import time
import subprocess
from actuator import log, util
from actuator.components import operator

def instructions():
    return {
        'counter': CounterSource,
        'string': StringSource,
        'int': IntegerSource,
        'bool': BooleanSource,
        'inflow': FlowSource,
    }

def build(instruction, kwargs):
    return instructions()[instruction](kwargs)
        
    
#interface
class Source(operator.Operator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def set_upstream(self, upstream):
        raise Exception("Source cannot have an upstream operator")

    def wire(self, inflows):
        pass

    #return a boolean
    @property
    def value(self):
        raise Exception("Unimplemented")
    


#Simple Source that takes a function and params
class FnSource(Source):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._fn = kwargs['fn']
        self._parameters = kwargs['args']
    
    #return a boolean
    @property
    def value(self):
        return self._fn(**self._parameters)


class DelegatingSource(Source):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._inner = kwargs.get('inner', None)

    @property
    def inner(self):
        return self._inner

    @property
    def name(self): 
        return "{}|{}".format(self.inner.name, type(self).__name__)



class FlowSource(Source):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._inflows = []
    
    def wire(self, inflows):
        self._inflows = inflows
    
    @property
    def value(self):
        #no inflows, return None
        if len(self._inflows) == 0: return None
        #one inflow, return the payload
        if len(self._inflows) == 1: return self._inflows[0].sink.get_payload()
        #more than one inflow, return a list of payloads
        return [i.sink.get_payload() for i in self._inflows]
            
    
    
    
class StringSource(Source):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._value = kwargs.get('value', 'yes')
        
    @property
    def value(self):
        return self._value

class IntegerSource(Source):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._value = int(kwargs.get('value', '1'))
        
    @property
    def value(self):
        return self._value

class BooleanSource(Source):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._value = util.parse_bool(wkargs.get('value', True))
        
    @property
    def value(self):
        return self._value


class CounterSource(Source):
    def __init__(self, *args, **kwargs):
        super().__init__(con*args, **kwargsfig)
        self._value = 0
        
    @property
    def value(self):
        value = self._value
        value += 1
        return value










class WeatherCanadaSource(Source):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._province = kwargs['province']
        self._citycode = kwargs['citycode']
        self._current = kwargs.get('current', None)
        self._low = kwargs.get('low', None)
        self._high = kwargs.get('high', None)
        if self._current: self._current = float(self._current)
        if self._low: self._low = float(self._low)
        if self._high: self._high = float(self._high)
        
        log.info("{name} received initial config {config}".format(name=self.name, config=(args, kwargs)))
    
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
        
        log.info("{name} received weather data: current={current}, high={high}, low={low}".format(name=self.name, current=current, low=low, high=high))
        
        if self._current != None:
            if self._current <= current: return False
        if self._low != None:
            if self._low <= low: return False
        if self._high != None:
            if self._high <= high: return False
            
        return True




