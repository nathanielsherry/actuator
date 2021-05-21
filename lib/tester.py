import time
import subprocess
from actuator import log, util, parser


DELAY_SHORT = 10
DELAY_MEDIUM = 120
DELAY_LONG = 3600


def instructions():
    return {
        'hourly': TimeTester,
        'locked': GDMLockTester,
        'process': ProcessConflictTester,
        'temp': TemperatureTester,
        'weather': WeatherTester,
        'url': URLTester,
        'cached': CachedTester,
        'try': TryTester,
        'smooth': SmoothTester,
        'epoch': EpochTester,
        'sh': ShellTester,
    }

def build(instruction, kwargs):
    return instructions()[instruction](kwargs)
        
    
#interface
class Tester(util.BaseClass):
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
    
        

class AllTester(Tester):
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


class AnyTester(Tester):
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


#Simple tester that takes a function and params
class FnTester(Tester):
    def __init__(self, config):
        self._fn = config['fn']
        self._parameters = config['args']
    
    #return a boolean
    @property
    def value(self):
        return self._fn(**self._parameters)


class DelegatingTester(Tester):
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
class SmoothTester(DelegatingTester):
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

        #get the result from the wrapped tester
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


class CachedTester(DelegatingTester):
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
        #the last poll of the inner tester, poll it now
        if time.time() > self._last_time + self.delay or self._last_value == None:
            log.debug("{name} checking inner value".format(name=self.name))
            self._last_time = time.time()
            self._last_value = self.inner.value
            
        return self._last_value


class ChangeTester(DelegatingTester):
    def __init__(self, config):
        super().__init__(config)
        self._state = None

    @property
    def value(self):
        old_state = self._state
        new_state = self.inner.value
        result = old_state == new_state
        self._state = new_state
        return result
        
        
class TryTester(DelegatingTester):
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




class GDMLockTester(Tester):
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
          


class TimeTester(Tester):
    def __init__(self, config):
        super().__init__(config)
        self._start = int(config['start'])
        self._end = int(config['end'])
    
    @property
    def delay(self): 
        return self._delay or DELAY_SHORT
    
    #return a boolean
    @property
    def value(self):
        import datetime
        now = datetime.datetime.now()
        h = now.hour
        
        if self._end < self._start:
            #end time is tomorrow
            return self._start <= h or h < self._end
        else:
            #end time is today
            return self._start <= h and h < self._end
        

class ProcessConflictTester(Tester):
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
    

class TemperatureTester(Tester):
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


class WeatherTester(Tester):
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
        

class URLTester(Tester):
    def __init__(self, config):
        super().__init__(config)
        self._url = config['url']
        self._text_only = util.parse_bool(config.get('text-only', 'false'))
        
    @property
    def delay(self): 
        return self._delay or 20
    
    @property
    def value(self):
        from html2text import html2text
        result = util.get_url(self._url)
        if self._text_only:
            result = html2text(result)
        
        
class EpochTester(Tester):
    def __init__(self, config):
        super().__init__(config)
        
    @property
    def value(self):
        return time.time()
        

class ShellTester(Tester):
    def __init__(self, config):
        super().__init__(config)
        self._args = config['args']
        
    @property
    def value(self):
        proc = subprocess.run(self._args, stdout=subprocess.PIPE)
        return proc.stdout.decode()
        
