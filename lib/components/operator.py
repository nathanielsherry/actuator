from actuator import util
from actuator.components import component


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
        'all': All,
        'any': Any,
        'str': Str,
        'int': Int,
        'float': Float,
        '_flowref': SubFlow,
    }
    
    

#interface
class Operator(component.Component):
    #upstream needs to be defined at creation time
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
        raise Exception("Unimplemented for {}".format(self.kind))
        
    @property
    def description_data(self):
        if self.upstream:
            return [self.upstream.description_data, self.kind]
        else:
            return self.kind
        

class Noop(Operator):
    @property
    def value(self):
        return self.upstream.value


class Equals(Operator):
    def initialise(self, *args, **kwargs):
        super().initialise(*args, **kwargs)
        self._to = args[0]

    @property
    def value(self):
        value = self.upstream.value
        if isinstance(self._to, (list, tuple)):
            return value in self._to
        else:
            return value == self._to


class Not(Operator):
    @property
    def value(self):
        value = self.upstream.value
        return not value

class Str(Operator):
    @property
    def value(self):
        return str(self.upstream.value)

class Int(Operator):
    @property
    def value(self):
        return int(self.upstream.value)
        
class Float(Operator):
    @property
    def value(self):
        return float(self.upstream.value)

class Get(Operator):
    def initialise(self, *args, **kwargs):
        super().initialise(*args, **kwargs)
        from actuator.lang import accessor
        self._accessor = accessor.accessor(args[0])
        
    @property
    def value(self):
        value = self.upstream.value
        return self._accessor(value)
        

class Has(Operator):
    def initialise(self, *args, **kwargs):
        super().initialise(*args, **kwargs)
        self._names = args
        
    @property
    def value(self):
        value = self.upstream.value
        for name in self._names:
            if name in value: return True
        return False

class All(Operator):           
    @property
    def value(self):
        value = self.upstream.value
        return all(value)


class Any(Operator):
    @property
    def value(self):
        value = self.upstream.value
        return any(value)


class SinkOperator(Operator):
    def __init__(self, sink):
        super().__init__()
        self._sink = sink
    
    def setup(self):
        super().setup()
        self.sink.setup()
    
    @property
    def sink(self): return self._sink
    
    @property
    def value(self):
        value = self.upstream.value
        self._sink.perform(value)
        return value

    @property
    def description_data(self):
        return {self.kind: {
            'sink': self.sink.description_data
        }}

class SubFlow(Operator):
    #Stash the target name early, so that once the context is set
    #we'll have everything we need to wire flows together
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._subflow_name = args[0]
        self._subflow = None

    @property
    def subflow_name(self): return self._subflow_name

    #Once the context is set, we have everything we need to look up
    #The target flow. This allows us to wire earlier
    def set_context(self, context):
        from actuator.components import monitor as mod_monitor
        super().set_context(context)
        flow = self.context
        flowset = flow.context
        self._subflow = flowset.get_flow(self.subflow_name)
        if not isinstance(self._subflow.monitor, mod_monitor.OnCallMonitor):
            raise Exception("Given flow {} is not callable".format(self._subflow.kind))

    @property
    def value(self):
        return self._subflow.monitor.call(self.upstream.value)


#Eliminates jitter from a value flapping a bit. The state starts as False and
#will switch when consistently the opposite for `delay[state]` seconds.
#delay is a dict with integer values for keys True and False
class Smooth(Operator):
    def initialise(self, *args, **kwargs):
        super().initialise(*args, **kwargs)
        
        delay = float(kwargs.get('delay', '10'))
        delay_true = float(kwargs.get('delay-true', delay))
        delay_false = float(kwargs.get('delay-false', delay))
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
    def initialise(self, *args, **kwargs):
        super().initialise(*args, **kwargs)
        self._last_time = 0
        self._last_value = None
        self._delay = float(kwargs.get('delay', '10'))

    @property
    def delay(self):
        return self._delay

    @property
    def value(self):
        #if it has been more than `delay` seconds since
        #the last poll of the upstream source, poll it now
        if time.time() > self._last_time + self.delay or self._last_value == None:
            log.debug("{kind} checking upstream value".format(kind=self.kind))
            self._last_time = time.time()
            self._last_value = self.upstream.value
            
        return self._last_value



class Forever(Operator):
    def initialise(self, *args, **kwargs):
        super().initialise(*args, **kwargs)
        self._value = None

    @property
    def value(self):
        if self._value == None:
            self._value = self.upstream.value            
        return self._value


class Once(Operator):
    def initialise(self, *args, **kwargs):
        super().initialise(*args, **kwargs)
        self._done = False

    @property
    def value(self):
        if self._done: return None
        self._done = True
        return self.upstream.value


class Change(Operator):
    def initialise(self, *args, **kwargs):
        super().initialise(*args, **kwargs)
        self._state = None

    @property
    def value(self):
        old_state = self._state
        new_state = self.upstream.value
        change = not (old_state == new_state)
        self._state = new_state
        return change


class Split(Operator):
    def initialise(self, *args, **kwargs):
        super().initialise(*args, **kwargs)
        self._delim = args[0]
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
    def initialise(self, *args, **kwargs):
        super().initialise(*args, **kwargs)
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
    def initialise(self, *args, **kwargs):
        super().initialise(*args, **kwargs)
        self._default = kwargs.get('default', 'false')

    @property
    def value(self):
        try:
            return self.upstream.value
        except:
            log.warn("{} threw an error, returning default value {}".format(self.upstream.kind, self._default))
            return self._default

class Hash(Operator):
    def initialise(self, *args, **kwargs):
        super().initialise(*args, **kwargs)
        self._algo = kwargs.get('algo', 'md5')
        
    @property
    def value(self):
        import hashlib
        m = hashlib.md5()
        value = self.upstream.value
        if isinstance(value, dict):
            value = value['state']
        m.update(str(value).encode())
        return m.hexdigest()
        


