#returns the inner object that has been decorated
def undecorate(decorated):
    #Not everything passed in will be decorated
    if not hasattr(decorated, '__closure__'): return decorated
    
    #Grab the contents of the decoration's closure
    contents = [cell.cell_contents for cell in decorated.__closure__]
    
    #First, we look for a class definition
    inner = [e for e in contents if isinstance(e, type)]
    if inner: return inner[0]
    
    #Then we look for another nested decorator, and recursively
    #undecorate it, too.
    from types import FunctionType
    inner = [e for e in contents if isinstance(e, FunctionType)]
    if inner: return undecorate(inner[0])
    
    return None

def register(cls, dec):
    cls = undecorate(cls)
    key = '__actuator_decorators'
    if not hasattr(cls, key): 
        setattr(cls, key, [])
    decs = getattr(cls, key)
    decs.append(dec)
    setattr(cls, key, decs)

def lookup(cls):
    cls = undecorate(cls)
    key = '__actuator_decorators'
    if not hasattr(cls, key): return []
    return getattr(cls, key)


class ConstructorHook:
    def __init__(self, name, ptype, default, desc):
        self._name = name
        self._ptype = ptype
        self._desc = desc
        self._default = default    
    
    @property
    def name(self): return self._name
    
    @property
    def ptype(self): return self._ptype
    
    @property
    def description(self): return self._desc
    
    @property
    def desc(self): return self.description
    
    @property
    def default(self): return self._default



class ParameterHook(ConstructorHook): pass

def parameter(name, ptype, default=None, desc=None):
    p = ParameterHook(name, ptype, default, desc)
    def inner(cls):
        def constructor(*args, **kwargs):
            instance = cls(*args, **kwargs)
            instance._add_parameter_hook(p)
            return instance
        register(cls, p)
        return constructor
    return inner

class ParameterSet:
    def __init__(self):
        self._params = {}
        
    def __getattr__(self, key):
        return self._params[key]
    
    def put(self, parameter, value):
        self._params[parameter.name] = value
        
    def default(self, parameter):
        self._params[parameter.name] = parameter.default
        
        
        
class ArgumentHook(ConstructorHook): pass
   
def argument(name, ptype, default=None, desc=None):
    a = ArgumentHook(name, ptype, default, desc)
    def inner(cls):
        def constructor(*args, **kwargs):
            instance = cls(*args, **kwargs)
            instance._add_argument_hook(a)
            return instance
        register(cls, a)
        return constructor
    return inner

class ArgumentList:
    def __init__(self):
        self._args = []
        self._namedargs = {}
        
    def __getitem__(self, index):
        return self._args[index]
    
    def __getattr__(self, key):
        return self._namedargs[key]
    
    def put(self, argument, value):
        self._args.append(value)
        self._namedargs[argument.name] = value
        
    def default(self, argument):
        self._args.append(argument.default)
        self._namedargs[argument.name] = argument.default
        
        
        

class IODescription:
    def __init__(self, ptype, description):
        self._ptype = ptype
        self._description = description
        
    @property
    def ptype(self): return self._ptype
    
    @property
    def description(self): return self._description

class InputDescription(IODescription):
    pass

def input(ptype, desc=None):
    def inner(cls):
        def constructor(*args, **kwargs):
            instance = cls(*args, **kwargs)
            d = InputDescription(ptype, desc)
            instance._add_input_description(d)
            return instance
        return constructor
    return inner

class OutputDescription(IODescription):
    pass

def output(ptype, desc=None):
    def inner(cls):
        def constructor(*args, **kwargs):
            instance = cls(*args, **kwargs)
            d = OutputDescription(ptype, desc)
            instance._add_output_description(d)
            return instance
        return constructor
    return inner
