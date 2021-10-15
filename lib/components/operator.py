from actuator import util
from actuator.components import component
from actuator.components.decorators import parameter, argument, input, output, allarguments

ROLE_OPERATOR = "operator"


def instructions():
    return {
        'hash': Hash,
        'change': Change,
        'cached': Cached,
        'try': Try,
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
        'real': Real,
        '_flowref': SubFlow,
        'map': MapFlow,
        'filter': FilterFlow,
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
        d = super().description_data
        if self.upstream: d[self.kind]["operator-upstream"] = self.upstream.description_data
        return d
    
    #Identifies this component as part of a flow
    @property
    def role(self): return ROLE_OPERATOR
    

@input('any', 'Accepts any input payload')
@output('any', 'Emits the given payload without modification')
class Noop(Operator):
    @property
    def value(self):
        return self.upstream.value

@input('any', 'Accepts any input payload')
@output('any', 'Emits the given payload without modification')
@argument('value', 'any', None, 'Value for comparison')
class Equals(Operator):
    """
    Compares the payload to a given value and emits the result
    """
    @property
    def value(self):
        value = self.upstream.value
        compare = self.args.value
        if isinstance(compare, (list, tuple)):
            return value in compare
        else:
            return value == compare


@input('bool', 'Boolean value to negate')
@output('bool', 'Negated input value')
class Not(Operator):
    """
    The boolean 'not' operator
    """
    @property
    def value(self):
        value = self.upstream.value
        return not value

@input('any')
@output('str')
class Str(Operator):
    """
    Convert payload to string
    """
    @property
    def value(self):
        return str(self.upstream.value)

@input('any')
@output('int')
class Int(Operator):
    """
    Convert payload to integer
    """
    @property
    def value(self):
        return int(self.upstream.value)

@input('any')
@output('real')
class Real(Operator):
    """
    Convert payload to real
    """
    @property
    def value(self):
        return float(self.upstream.value)

@input('any', 'Object or data structure')
@output('any', 'Value accessed from within object or data structure')
@argument('accessor', 'str, list', [], 'Accessor string or list of keys')
class Get(Operator):
    """
    Given an accessor string or list of keys, looks up a value 
    from within the payload, the location of which is described by the 
    accessor.
    
    For example, assume we have payloads with the following structure::
    
          payload = ['a', 'b', {'c': 'value'}]
    
    We can access the string 'value' with the accessor string '2.c'::
    
          get('2.c')
        
    Or with the list of keys [2, 'c']::
    
          get([2, 'c'])
          

    """
    def initialise(self, *args, **kwargs):
        from actuator.lang.accessor import accessor
        self._access_function = accessor(self.args.accessor)
        
    @property
    def value(self):
        value = self.upstream.value
        return self._access_function(value)
        

@input('any', 'Object or data structure')
@output('bool', 'Indicates if any match was found')
@allarguments('keys')
class Has(Operator):
    """
    Given a list of keys, emit True if any of them are contained within the payload
    """       
    @property
    def value(self):
        value = self.upstream.value
        return any([key in value for key in self.args.keys])

@input('list', 'Elements to evaluate')
@output('bool', 'Indicates if all elements evaluate to true or truthy')
class All(Operator):   
    """
    Given a list or iterable, emit True if all elements evaluate to True or truthy
    """            
    @property
    def value(self):
        value = self.upstream.value
        return all(value)


@input('list', 'Elements to evaluate')
@output('bool', 'Indicates if any elements evaluate to true or truthy')
class Any(Operator):
    """
    Given a list or iterable, emit True if any elements evaluate to True or truthy
    """ 
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
        d = super().description_data
        if self.sink: d[self.kind]["sinkoperator-target"] = self.sink.description_data
        return d


class SubFlow(Operator):
    #Stash the target name early, so that once the context is set
    #we'll have everything we need to wire flows together
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._flowref = args[0]
        self._subflow_name = args[0].reference
        self._subflow = None

    @property
    def subflow_name(self): return self._subflow_name

    @property
    def subflow(self): return self._subflow

    #Once the context is set, we have everything we need to look up
    #The target flow. This allows us to wire earlier
    def set_context(self, context):
        from actuator.components import monitor as mod_monitor
        super().set_context(context)
        self._subflow = self._flowref.dereference(context.context)
        if not isinstance(self.subflow.monitor, mod_monitor.OnCallMonitor):
            raise Exception("Given flow {} is not callable".format(self.subflow.kind))

    @property
    def value(self):
        return self.subflow.monitor.call(self.upstream.value)


class MapFlow(SubFlow):
    @property
    def value(self):
        return [self.subflow.monitor.call(v) for v in self.upstream.value]

class FilterFlow(SubFlow):
    @property
    def value(self):
        return [v for v in self.upstream.value if self.subflow.monitor.call(v)]

    

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
            self.logger.debug("Checking upstream value")
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
            self.logger.warn("Caught error, returning default value %s", self._default)
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
        


