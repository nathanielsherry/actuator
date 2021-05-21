import time
import subprocess
from actuator import log, util, parser


DELAY_SHORT = 10
DELAY_MEDIUM = 120
DELAY_LONG = 3600


def instructions():
    return {
        'during': DuringState,
        'time': TimeState,
        'locked': GDMLockState,
        'process': ProcessConflictState,
        'temp': TemperatureState,
        'weather': WeatherState,
        'url': URLState,
        'file': FileState,
        'cached': CachedState,
        'try': TryState,
        'smooth': SmoothState,
        'epoch': EpochState,
        'sh': ShellState,
        'hash': HashState,
        'change': ChangeState,
    }

def build(instruction, kwargs):
    return instructions()[instruction](kwargs)
        
    
#interface
class State(util.BaseClass):
    def __init__(self, config=None):
        if config:
            self._delay = config.get('delay', None)
            if self._delay: self._delay = float(self._delay)
    
    @property
    def delay(self):
        return self._delay or DELAY_MEDIUM
    
    #return a boolean
    @property
    def value(self):
        raise Exception("Unimplemented")
    
        

class AllState(State):
    def __init__(self, tests):
        if any([t == None for t in tests]): 
            raise Exception("Test cannot be None")
        self._tests = tests
        
    @property
    def delay(self): 
        return min([t.delay for t in self._tests])
    
    #return a boolean
    @property
    def value(self):
        return all([t.value for t in self._tests])

    @property
    def name(self): return "[{}]|All".format(",".join([t.name for t in self._tests]))


class AnyState(State):
    def __init__(self, tests):
        if any([t == None for t in tests]): 
            raise Exception("Test cannot be None")
        self._tests = tests
        
    @property
    def delay(self): 
        return min([t.delay for t in self._tests])
    
    #return a boolean
    @property
    def value(self):
        return any([t.value for t in self._tests])
        
    @property
    def name(self): return "[{}]|Any".format(",".join([t.name for t in self._tests]))


#Simple State that takes a function and params
class FnState(State):
    def __init__(self, config):
        self._fn = config['fn']
        self._parameters = config['args']
    
    #return a boolean
    @property
    def value(self):
        return self._fn(**self._parameters)


class DelegatingState(State):
    def __init__(self, config):
        super().__init__(config)
        self._inner = config['inner']
        if not self.inner:
            raise Exception("Inner cannot be None")

    @property
    def inner(self):
        return self._inner
    
    @property
    def delay(self):
        return self._delay or self.inner.delay

    @property
    def name(self): 
        return "{}|{}".format(self.inner.name, type(self).__name__)


#Eliminates jitter from a value flapping a bit. The state starts as False and
#will switch when consistently the opposite for `delay[state]` seconds.
#delay is a dict with integer values for keys True and False
class SmoothState(DelegatingState):
    def __init__(self, config):
        super().__init__(config)
        
        delay = float(config.get('delay', '30'))
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


class CachedState(DelegatingState):
    def __init__(self, config):
        super().__init__(config)
        self._last_time = 0
        self._last_value = None

    @property
    def delay(self):
        return self._delay or DELAY_MEDIUM

    @property
    def value(self):
        #if it has been more than `delay` seconds since
        #the last poll of the inner state, poll it now
        if time.time() > self._last_time + self.delay or self._last_value == None:
            log.debug("{name} checking inner value".format(name=self.name))
            self._last_time = time.time()
            self._last_value = self.inner.value
            
        return self._last_value


class ChangeState(DelegatingState):
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
        
        
class TryState(DelegatingState):
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

class HashState(DelegatingState):
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
        



class GDMLockState(State):
    def __init__(self, config):
        super().__init__(config)
        self._session = config['session']
    
    @property
    def delay(self): 
        return self._delay or DELAY_SHORT
    
    #return a boolean
    @property
    def value(self):
        result = subprocess.run("loginctl show-session {} | grep LockedHint | cut -d = -f 2".format(self._session), shell=True, capture_output=True)
        stdout = result.stdout.decode().strip()
        return stdout == "yes"  
          

class TimeState(State):
    def __init__(self, config):
        super().__init__(config)
        self._format = config.get('format', '%H:%M:%S')
        
    @property
    def delay(self): 
        return self._delay or DELAY_SHORT
        

    #return a boolean
    @property
    def value(self):
        import datetime
        now = datetime.datetime.now().time()
        return now.strftime(self._format)

class DuringState(State):
    def __init__(self, config):
        super().__init__(config)
        self._start = TimeState.parse(config['start'])
        self._end = TimeState.parse(config['end'])
    
    @staticmethod
    def parse(s):
        from dateutil import parser
        return parser.parse(s).time()
    
    @property
    def delay(self): 
        return self._delay or DELAY_SHORT
    
    #return a boolean
    @property
    def value(self):
        import datetime
        now = datetime.datetime.now().time()
        
        if self._end < self._start:
            #end time is tomorrow
            return self._start <= now or now < self._end
        else:
            #end time is today
            return self._start <= now and now < self._end
        

class ProcessConflictState(State):
    def __init__(self, config):
        super().__init__(config)
        self._names = parser.parse_args_list(config['names'])
    
    @property
    def delay(self): 
        return self._delay or 60
    
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
    

class TemperatureState(State):
    def __init__(self, config):
        super().__init__(config)
        self._cutoff = float(config['cutoff'])
    
    @property
    def delay(self): 
        return self._delay or 600
    
    @property
    def value(self):
        #try:
        import temper
        t = temper.Temper()
        return t.read[0]['internal temperature'] <= self._cutoff
        #except:
        #    return True


class WeatherState(State):
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
    def delay(self): 
        return self._delay or 900
    
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
        

class URLState(State):
    def __init__(self, config):
        super().__init__(config)
        self._url = config['args'][0]
        self._text_only = util.parse_bool(config.get('html-to-text', 'false'))
        
    @property
    def delay(self): 
        return self._delay or DELAY_MEDIUM
    
    @property
    def value(self):
        result = util.get_url(self._url)
        if self._text_only:
            from html2text import html2text
            result = html2text(result)
        return result
        

class FileState(State):
    def __init__(self, config):
        super().__init__(config)
        self._filename = config['args'][0]
        self._binary = util.parse_bool(config.get('binary', 'false'))

    @property
    def delay(self): 
        return self._delay or DELAY_MEDIUM
    
    @property
    def value(self):
        read_string = 'r'
        if self._binary: read_string = 'rb'
        fh = open(self._filename, read_string)
        contents = fh.read()
        fh.close()
        return contents

        
class EpochState(State):
    def __init__(self, config):
        super().__init__(config)
        
    @property
    def value(self):
        return time.time()
        

class ShellState(State):
    def __init__(self, config):
        super().__init__(config)
        self._args = config['args']
        
    @property
    def value(self):
        proc = subprocess.run(self._args, stdout=subprocess.PIPE)
        return proc.stdout.decode()
        
        

