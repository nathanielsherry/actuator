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
    def __init__(self, name, ptype, default, desc, parser=None):
        self._name = name
        self._ptype = ptype
        self._desc = desc
        self._default = default
        self._parser = parser
    
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
    
    @property
    def parser(self): return self._parser




class ParameterSet:
    def __init__(self):
        self._params = {}
        
    def __getattr__(self, key):
        return self._params[key]
    
    def put(self, parameter, value):
        self._params[parameter.name] = value
    
    @property
    def as_dict(self):
        return dict(self._params)

class ParameterHook(ConstructorHook):
    def consume(self, parameterset, **kwargs):
        if self.name in kwargs:
            param_value = kwargs[self.name]
            if self.parser:
                param_value = self.parser(param_value)
            parameterset.put(self, param_value)
            del kwargs[self.name]
        else:
            parameterset.put(self, self.default)
        return kwargs
    
def parameter(name, ptype, default=None, desc=None, parser=None):
    p = ParameterHook(name, ptype, default, desc, parser)
    def inner(cls):
        class ParameterDecorator(cls):
            def construct(self):
                super()._add_parameter_hook(p)
            @classmethod
            def get_source(cls):
                return cls.__bases__[0].get_source()
                
        register(cls, p)
        return ParameterDecorator
    return inner


class AllParametersHook(ParameterHook):
    def __init__(self, name):
        super().__init__(name, 'dict', {}, 'All remeaining named arguments')
    def consume(self, parameterset, **kwargs):
        parameterset.put(self, kwargs)
        return {}

def allparameters(name):
    p = AllParametersHook(name)
    def inner(cls):
        class AllParametersDecorator(cls):
            def construct(self):
                super()._add_parameter_hook(p)
            @classmethod
            def get_source(cls):
                return cls.__bases__[0].get_source()
                
        register(cls, p)
        return AllParametersDecorator
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
    
    @property
    def as_list(self): 
        return self._args[:]
        

class ArgumentHook(ConstructorHook):
    def consume(self, argumentlist, *args):
        if len(args):
            arg_value = args[0]
            if self.parser:
                arg_value = self.parser(arg_value)
            argumentlist.put(self, arg_value)
            args = args[1:]
        else:
            argumentlist.put(self, self.default)
        return args
   
def argument(name, ptype, default=None, desc=None, parser=None):
    a = ArgumentHook(name, ptype, default, desc, parser)
    def inner(cls):
        class ArgumentDecorator(cls):
            def construct(self):
                super()._add_argument_hook(a)
            @classmethod
            def get_source(cls):
                return cls.__bases__[0].get_source()
                
        register(cls, a)
        return ArgumentDecorator
    return inner


class AllArgumentsHook(ArgumentHook):
    def __init__(self, name):
        super().__init__(name, 'list', [], 'All remeaining positional arguments')
    def consume(self, argumentlist, *args):
        argumentlist.put(self, args)
        return []
   
def allarguments(name):
    a = AllArgumentsHook(name)
    def inner(cls):
        class AllArgumentsDecorator(cls):
            def construct(self):
                super()._add_argument_hook(a)
            @classmethod
            def get_source(cls):
                return cls.__bases__[0].get_source()
                
        register(cls, a)
        return AllArgumentsDecorator
    return inner




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
    d = InputDescription(ptype, desc)
    def inner(cls):
        class InputDecorator(cls):
            def construct(self):
                super()._set_input_description(d)
            @classmethod
            def get_source(cls):
                return cls.__bases__[0].get_source()
                
        register(cls, d)
        return InputDecorator
    return inner

class OutputDescription(IODescription):
    pass

def output(ptype, desc=None):
    d = OutputDescription(ptype, desc)
    def inner(cls):
        class OutputDecorator(cls):
            def construct(self):
                super()._set_output_description(d)
            @classmethod
            def get_source(cls):
                return cls.__bases__[0].get_source()
                
        register(cls, d)
        return OutputDecorator
    return inner



def source(fn):
    from actuator.components.source import Source
    class FunctionSource(Source):
        @property
        def value(self):
            args = self.args.as_list
            params = self.params.as_dict
            return fn(*args, **params)
        @classmethod
        def get_source(cls):
            import inspect
            return inspect.getsource(fn)
        @classmethod
        def get_docstring(cls):
            import inspect
            docstring = inspect.getdoc(fn)
            if docstring: docstring = inspect.cleandoc(docstring)
            return docstring
    return FunctionSource


def sink(fn):
    from actuator.components.sink import Sink
    class FunctionSink(Sink):
        def perform(self, payload):
            args = self.args.as_list
            params = self.params.as_dict
            return fn(payload, *args, **params)
        @classmethod
        def get_source(cls):
            import inspect
            return inspect.getsource(fn)
        @classmethod
        def get_docstring(cls):
            import inspect
            docstring = inspect.getdoc(fn)
            if docstring: docstring = inspect.cleandoc(docstring)
            return docstring
    return FunctionSink


def operator(fn):
    from actuator.components.operator import Operator
    class FunctionOperator(Operator):
        @property
        def value(self):
            args = self.args.as_list
            params = self.params.as_dict
            return fn(self.upstream.value, *args, **params)
        @classmethod
        def get_source(cls):
            import inspect
            return inspect.getsource(fn)
        @classmethod
        def get_docstring(cls):
            import inspect
            docstring = inspect.getdoc(fn)
            if docstring: docstring = inspect.cleandoc(docstring)
            return docstring
    return FunctionOperator
