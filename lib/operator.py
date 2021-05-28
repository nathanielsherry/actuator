from actuator import util


def instructions():
    return {
        'hash': Hash,
        'change': Change,
        'cached': Cached,
        'try': Try,
        'smooth': Smooth,
        'forever': Forever,
        'once': Once,
        'split': Split,
        'noop': Noop,
        'feed': Feed,
        'eq': Equals,
        'not': Not,
        'get': Get,
        'has': Has,
    }
    
    

#interface
class Operator(util.BaseClass):
    def __init__(self, config):
        super().__init__(config)
        self._upstream = None
    
    def set_upstream(self, upstream):
        self._upstream = upstream
    
    @property
    def upstream(self): return self._upstream
    
    @property
    def upstreams(self):
        if self.upstream == None: return [self]
        return self.upstream.upstreams + [self]
    
    #return a boolean
    @property
    def value(self):
        raise Exception("Unimplemented")
        

class Noop(Operator):
    def __init__(self, config):
        super().__init__(config)

    @property
    def value(self):
        return self.upstream.value


class Equals(Operator):
    def __init__(self, config):
        super().__init__(config)
        self._to = config['args'][0]

    @property
    def value(self):
        value = self.upstream.value
        if isinstance(self._to, (list, tuple)):
            return value in self._to
        else:
            return value == self._to


class Not(Operator):
    def __init__(self, config):
        super().__init__(config)

    @property
    def value(self):
        value = self.upstream.value
        return not value

class Get(Operator):
    def __init__(self, config):
        from actuator import accessor
        super().__init__(config)
        self._accessor = accessor.accessor(config['args'][0])
        
    @property
    def value(self):
        value = self.upstream.value
        return self._accessor(value)
        

class Has(Operator):
    def __init__(self, config):
        super().__init__(config)
        self._names = config['args']
        
    @property
    def value(self):
        value = self.upstream.value
        for name in self._names:
            if name in value: return True
        return False

        
#Eliminates jitter from a value flapping a bit. The state starts as False and
#will switch when consistently the opposite for `delay[state]` seconds.
#delay is a dict with integer values for keys True and False
class Smooth(Operator):
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
        new_result = self.upstream.value
        
        if new_result != self._last:
            #reset the last change time last known status
            self._last_time = time.time()
            self._last = new_result
        
        #If the state doesn't match the last `delay` seconds, flip it
        time_delta = time.time() - self._last_time
        if self._last != self._state and self._lag[self._last] >= time_delta:
            self._state = self._last
            
        return self._state
    
    

class Cached(Operator):
    def __init__(self, config):
        super().__init__(config)
        self._last_time = 0
        self._last_value = None
        self._delay = float(config.get('delay', '10'))

    @property
    def delay(self):
        return self._delay

    @property
    def value(self):
        #if it has been more than `delay` seconds since
        #the last poll of the upstream source, poll it now
        if time.time() > self._last_time + self.delay or self._last_value == None:
            log.debug("{name} checking upstream value".format(name=self.name))
            self._last_time = time.time()
            self._last_value = self.upstream.value
            
        return self._last_value



class Forever(Operator):
    def __init__(self, config):
        super().__init__(config)
        self._value = None

    @property
    def value(self):
        if self._value == None:
            self._value = self.upstream.value            
        return self._value


class Once(Operator):
    def __init__(self, config):
        super().__init__(config)
        self._done = False

    @property
    def value(self):
        if self._done: return None
        self._done = True
        return self.upstream.value


class Change(Operator):
    def __init__(self, config):
        super().__init__(config)
        self._state = None

    @property
    def value(self):
        old_state = self._state
        new_state = self.upstream.value
        change = not (old_state == new_state)
        self._state = new_state
        return change


class Split(Operator):
    def __init__(self, config):
        super().__init__(config)
        self._delim = config.get('delim', '\n')
        self._parts = []

    @property
    def value(self):
        value = self.upstream.value
        if value == None: return None
        if not isinstance(value, str): value = str(value)
        return value.split(self._delim)
                

#Accepts a list and produces one item from that list until done, then repeats
#TODO: expand this to cover iterables, dict kv pairs, etc
class Feed(Operator):
    def __init__(self, config):
        super().__init__(config)
        self._parts = []

    @property
    def value(self):
        #If we're not working on a previous list, fetch the next one now
        while not self._parts:
            value = self.upstream.value
            if value == None: return None
            if not isinstance(value, list): value = list(value)
            self._parts = value
        #Return the next item in the list
        value = self._parts[0]
        self._parts = self._parts[1:]
        return value

        
class Try(Operator):
    def __init__(self, config):
        super().__init__(config)
        self._default = config.get('default', 'false')

    @property
    def value(self):
        try:
            return self.upstream.value
        except:
            log.warn("{} threw an error, returning default value {}".format(self.upstream.name, self._default))
            return self._default

class Hash(Operator):
    def __init__(self, config):
        super().__init__(config)
        self._algo = config.get('algo', 'md5')
        
    @property
    def value(self):
        import hashlib
        m = hashlib.md5()
        value = self.upstream.value
        if isinstance(value, dict):
            value = value['state']
        m.update(str(value).encode())
        return m.hexdigest()
        


