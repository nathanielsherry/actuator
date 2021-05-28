import time
import subprocess
from actuator import log, util, operator

def instructions():
    return {
        'temp': TemperatureSource,
        'counter': CounterSource,
        'string': StringSource,
        'int': IntegerSource,
    }

def build(instruction, kwargs):
    return instructions()[instruction](kwargs)
        
    
#interface
class Source(operator.Operator):
    def __init__(self, config):
        super().__init__(config)
    
    def set_upstream(self, upstream):
        raise Exception("Source cannot have an upstream operator")

    #return a boolean
    @property
    def value(self):
        raise Exception("Unimplemented")
    
        

class AllSource(Source):
    def __init__(self, tests):
        if any([t == None for t in tests]): 
            raise Exception("Test cannot be None")
        self._tests = tests
            
    #return a boolean
    @property
    def value(self):
        return all([t.value for t in self._tests])

    @property
    def name(self): return "[{}]|All".format(",".join([t.name for t in self._tests]))


class AnySource(Source):
    def __init__(self, tests):
        if any([t == None for t in tests]): 
            raise Exception("Test cannot be None")
        self._tests = tests
        
    #return a boolean
    @property
    def value(self):
        return any([t.value for t in self._tests])
        
    @property
    def name(self): return "[{}]|Any".format(",".join([t.name for t in self._tests]))


#Simple Source that takes a function and params
class FnSource(Source):
    def __init__(self, config):
        self._fn = config['fn']
        self._parameters = config['args']
    
    #return a boolean
    @property
    def value(self):
        return self._fn(**self._parameters)


class DelegatingSource(Source):
    def __init__(self, config):
        super().__init__(config)
        self._inner = config.get('inner', None)

    @property
    def inner(self):
        return self._inner

    @property
    def name(self): 
        return "{}|{}".format(self.inner.name, type(self).__name__)



    
    
class StringSource(Source):
    def __init__(self, config):
        super().__init__(config)
        self._value = config.get('value', 'yes')
        
    @property
    def value(self):
        return self._value

class IntegerSource(Source):
    def __init__(self, config):
        super().__init__(config)
        self._value = int(config.get('value', '1'))
        
    @property
    def value(self):
        return self._value


class CounterSource(Source):
    def __init__(self, config):
        super().__init__(config)
        self._value = 0
        
    @property
    def value(self):
        value = self._value
        value += 1
        return value







class TemperatureSource(Source):
    def __init__(self, config):
        super().__init__(config)
        self._cutoff = float(config['cutoff'])

    @property
    def value(self):
        #try:
        import temper
        t = temper.Temper()
        return t.read[0]['internal temperature'] <= self._cutoff
        #except:
        #    return True


class WeatherCanadaSource(Source):
    def __init__(self, config):
        super().__init__(config)
        self._province = config['province']
        self._citycode = config['citycode']
        self._current = config.get('current', None)
        self._low = config.get('low', None)
        self._high = config.get('high', None)
        if self._current: self._current = float(self._current)
        if self._low: self._low = float(self._low)
        if self._high: self._high = float(self._high)
        
        log.info("{name} received initial config {config}".format(name=self.name, config=config))
    
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




