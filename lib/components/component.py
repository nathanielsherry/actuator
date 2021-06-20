
class Component:
    def __init__(self, *args, **kwargs):
        self.__component_args = list(args)
        self.__component_kwargs = dict(kwargs)
        
        
        #Run mixin init methods if this is the first superclass 
        #and there are others after it
        supers = self.__class__.mro()
        supers = supers[supers.index(Component)+1:]
        while True:
            if supers[0] == object: break
            supers[0].__init__(self, *args, **kwargs)
            supers = supers[1:]
        
        self._context = None
    
    #At creation time, args and kwargs are stashed until such time as 
    #they can be loaded and interpereted within the context in which 
    #this component will be run
    def setup(self):
        args = list(self.__component_args)
        kwargs = dict(self.__component_kwargs)
        
        def deref(o):
            from actuator.lang.construct import VariableReference
            if isinstance(o, VariableReference): 
                return o.dereference(self.context.context)
            else:
                return o
        
        args = [deref(arg) for arg in args]
        kwargs = {k: deref(v) for k, v in kwargs.items()}
        
        #Call the standard initialise method
        result = self.initialise(*args, **kwargs)
        
        if not result == False:
            #Call mixin initialise methods
            supers = self.__class__.mro()
            supers = supers[supers.index(Component)+1:]
            while True:
                if supers[0] == object: break
                supers[0].initialise(self, *args, **kwargs)
                supers = supers[1:]
    
    def initialise(self, *args, **kwargs):
        return

    def start(self): return
    def stop(self): return

    @property
    def name(self): return None
    
    #Returns information about the specific class this object belongs to
    @property
    def kind(self):
        return type(self).__name__
    
    #Identifies this component as part of a flow
    @property
    def role(self): return None
    
    def __repr__(self):
        return "<{name}>".format(name=self.kind)
    def __str__(self):
        return self.kind
    
    @property
    def context(self): return self._context
    
    def set_context(self, context):
        self._context = context
    
    @property
    def description_data(self):
        return {self.kind: {
            "name": self.name,
            "role": self.role,
            "args": self.__component_args,
            "kwargs": dict(self.__component_kwargs),
        }}

    @property
    def description(self):
        import yaml
        return yaml.dump(self.description_data)
        
        
class ComponentMixin:
    def __init__(self, *args, **kwargs):
        pass
    
    def initialise(self, *args, **kwargs):
        pass
