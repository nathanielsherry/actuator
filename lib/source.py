import time
import subprocess
from actuator import log, util


#DELAY_SHORT = 2
#DELAY_MEDIUM = 60
#DELAY_LONG = 3600


def instructions():
    return {
        'hash': HashSource,
        'change': ChangeSource,
        'cached': CachedSource,
        'try': TrySource,
        'smooth': SmoothSource,
        'locked': GDMLockSource,
        'process': ProcessConflictSource,
        'temp': TemperatureSource,
        'weather': WeatherSource,
        'file': FileSource,

    }

def build(instruction, kwargs):
    return instructions()[instruction](kwargs)
        
    
#interface
class Source(util.BaseClass):
    def __init__(self, config):
        super().__init__(config)
           
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
        self._inner = config['inner']
        if not self.inner:
            raise Exception("Inner cannot be None")

    @property
    def inner(self):
        return self._inner

    @property
    def name(self): 
        return "{}|{}".format(self.inner.name, type(self).__name__)


#Eliminates jitter from a value flapping a bit. The state starts as False and
#will switch when consistently the opposite for `delay[state]` seconds.
#delay is a dict with integer values for keys True and False
class SmoothSource(DelegatingSource):
    def __init__(self, config):
        super().__init__(config)
        
        delay = float(config.get('delay', '10'))
        delay_true = float(config.get('delay-true', delay))
        delay_false = float(config.get('delay-false', delay))
        self._lag = {True: delay_true, False: delay_false}
        
        self._last_time = time.time()
        self._last = False
        self._state = False


    @property
    def value(self):

        #get the result from the wrapped state
        new_result = self.inner.value
        
        if new_result != self._last:
            #reset the last change time last known status
            self._last_time = time.time()
            self._last = new_result
        
        #If the state doesn't match the last `delay` seconds, flip it
        time_delta = time.time() - self._last_time
        if self._last != self._state and self._lag[self._last] >= time_delta:
            self._state = self._last
            
        return self._state


class CachedSource(DelegatingSource):
    def __init__(self, config):
        super().__init__(config)
        self._last_time = 0
        self._last_value = None
        self._delay = config.get('delay', '10')

    @property
    def delay(self):
        return self._delay

    @property
    def value(self):
        #if it has been more than `delay` seconds since
        #the last poll of the inner source, poll it now
        if time.time() > self._last_time + self.delay or self._last_value == None:
            log.debug("{name} checking inner value".format(name=self.name))
            self._last_time = time.time()
            self._last_value = self.inner.value
            
        return self._last_value


class ChangeSource(DelegatingSource):
    def __init__(self, config):
        super().__init__(config)
        self._state = None

    @property
    def value(self):
        old_state = self._state
        new_state = self.inner.value
        change = not (old_state == new_state)
        self._state = new_state
        return change
        
        
class TrySource(DelegatingSource):
    def __init__(self, config):
        super().__init__(config)
        self._default = config.get('default', 'false')

    @property
    def value(self):
        try:
            return self.inner.value
        except:
            log.warn("{} threw an error, returning default value {}".format(self.inner.name, self._default))
            return self._default

class HashSource(DelegatingSource):
    def __init__(self, config):
        super().__init__(config)
        self._algo = config.get('algo', 'md5')
        
    @property
    def value(self):
        import hashlib
        m = hashlib.md5()
        value = self.inner.value
        if isinstance(value, dict):
            value = value['state']
        m.update(str(value).encode())
        return m.hexdigest()
        



class GDMLockSource(Source):
    def __init__(self, config):
        super().__init__(config)
        self._session = config['session']
    
    #return a boolean
    @property
    def value(self):
        result = subprocess.run("loginctl show-session {} | grep LockedHint | cut -d = -f 2".format(self._session), shell=True, capture_output=True)
        stdout = result.stdout.decode().strip()
        return stdout == "yes"  
          


class ProcessConflictSource(Source):
    def __init__(self, config):
        super().__init__(config)
        self._names = config['args']

    #return a boolean
    @property
    def value(self):
        import psutil
        if not self._names: return True
        for proc in psutil.process_iter(['name']):
            procname = proc.name()
            if procname in self._names:
                log.info("{name} found {process}".format(name=self.name, process=procname)) 
                return False
        return True
    

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

class WeatherSource(Source):
    def __init__(self, config):
        super().__init__(config)
        coords = config['coords']
        lat, lon = coords.split(',')
        lat = float(lat)
        lon = float(lon)
        self._id = WeatherSource.lookup_coords(lat, lon)
        self._days = int(config.get('days', '3'))
        self._low = config.get('low', None)
        self._high = config.get('high', None)
        if self._low: self._low = float(self._low)
        if self._high: self._high = float(self._high)
        
        log.info("{name} received initial config {config}".format(name=self.name, config=config))

    @staticmethod
    def lookup_coords(lat, lon):
        import json
        url = "https://www.metaweather.com/api/location/search/?lattlong={},{}".format(lat, lon)
        log.debug("WeatherSource looking up weather data from {}".format(url))
        doc = util.get_url(url)
        data = json.loads(doc)
        return int(data[0]['woeid'])


    @property
    def value(self):
        import json
        document = util.get_url("https://www.metaweather.com/api/location/{id}/".format(id=self._id))
        data = json.loads(document)
        forecast = data['consolidated_weather'][:self._days]
        high = max([day['max_temp'] for day in forecast])
        low = max([day['max_temp'] for day in forecast])
        log.info("{name} received weather data: high={high}, low={low}".format(name=self.name, low=low, high=high))

        if self._low != None:
            if self._low <= low: return False
        if self._high != None:
            if self._high <= high: return False
            
        return True



        

class FileSource(Source):
    def __init__(self, config):
        super().__init__(config)
        self._filename = config['args'][0]
        self._binary = util.parse_bool(config.get('binary', 'false'))

    @property
    def value(self):
        read_string = 'r'
        if self._binary: read_string = 'rb'
        fh = open(self._filename, read_string)
        contents = fh.read()
        fh.close()
        return contents

        

        


        
        


