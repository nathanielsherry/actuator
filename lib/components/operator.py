from actuator import util
from actuator.components import component
from actuator.components.decorators import parameter, argument, input, output, allarguments, operator

ROLE_OPERATOR = "operator"


def instructions():
    return {
        'hash': do_hash,
        'change': Change,
        'cached': Cached,
        'try': Try,
        'forever': Forever,
        'once': Once,
        'split': split,
        'noop': noop,
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
    def construct(self):
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
@operator
def noop(payload):
    return payload

@input('any', 'Accepts any input payload')
@output('any', 'Emits the given payload without modification')
@argument('value', 'any', None, 'Value for comparison')
@operator
class Equals(Operator):
    @property
    def value(self):
        """
        Compares the payload to a given value and emits the result
        """
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
    def construct(self):
        self._value = None

    @property
    def value(self):
        if self._value == None:
            self._value = self.upstream.value            
        return self._value


class Once(Operator):
    def construct(self):
        self._done = False

    @property
    def value(self):
        if self._done: return None
        self._done = True
        return self.upstream.value


class Change(Operator):
    def construct(self):
        self._state = None

    @property
    def value(self):
        old_state = self._state
        new_state = self.upstream.value
        change = not (old_state == new_state)
        self._state = new_state
        return change

@input('any', 'String to be split, converted to string if other')
@output('list[str]', 'List of split string segments')
@argument('delim', 'str', '\n', 'Delimiter by which to split the payload')
@operator
def split(payload, delim):
    if payload == None: return None
    if not isinstance(payload, str): 
        payload = str(payload)
    return payload.split(delim)
                

@input('any', 'Accepts any payload')
@output('any', 'Outputs any payload, or the given default if an exception was thrown')
@parameter('default', 'any', False, 'Default value to return on failure')
class Try(Operator):
    @property
    def value(self):
        try:
            return self.upstream.value
        except:
            self.logger.warn("Caught error, returning default value %s", self.params.default)
            return self.params.default

@input('any', 'Any payload will be converted to a string')
@output('str', 'md5 hex digest of the payload')
@operator
def do_hash(payload):
    import hashlib
    m = hashlib.md5()
    m.update(str(payload).encode())
    return m.hexdigest()
    


