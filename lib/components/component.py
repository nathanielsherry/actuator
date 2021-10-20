from actuator import log

class Parameterisable:
    def __init__(self, *args, **kwargs):
        self.__parameterhooks = []
        from actuator.components.decorators import ParameterSet
        self._parameters = ParameterSet()
        
        self.__argumenthooks = []
        from actuator.components.decorators import ArgumentList
        self._arguments = ArgumentList()
    
    @property
    def parameters(self): return self._parameters
    
    @property
    def params(self): return self.parameters
    
    def _get_parameter_hooks(self): return self.__parameterhooks[:]
    
    def _add_parameter_hook(self, parameter):
        if parameter.name in self.__parameterhooks:
            raise Exception("Parameter {} already registered", parameter.name)
        self.__parameterhooks.append(parameter)
        
    @property
    def arguments(self): return self._arguments
    
    @property
    def args(self): return self.arguments
    
    def _get_argument_hooks(self): return self.__argumenthooks[:]
    
    def _add_argument_hook(self, argument):
        #Arguments will be processed in reverse order due to 
        #decorator processing order
        self.__argumenthooks.insert(0, argument)

class Initialisable:
    def initialise(self, *args, **kwargs):
        pass
    
    def _perform_init(self, __base_class, *args, **kwargs):
        #Run mixin init methods if this is the first superclass 
        #and there are others after it
        supers = self.__class__.mro()
        supers = supers[supers.index(__base_class)+1:]
        while True:
            if supers[0] == object: break
            if supers[0] == Initialisable:
                supers = supers[1:]
                continue
            if '__init__' in vars(supers[0]):
                supers[0].__init__(self, *args, **kwargs)
            supers = supers[1:]
            
        
    def _perform_initialise(self, __base_class, *args, **kwargs):
        #Call mixin initialise methods
        supers = self.__class__.mro()
        supers = supers[supers.index(__base_class)+1:]
        while True:
            if supers[0] == object: break
            self.logger.debug("Calling initialise on mixin %s", str(supers[0]))
            if issubclass(supers[0], Initialisable) and 'initialise' in vars(supers[0]):
                supers[0].initialise(self, *args, **kwargs)
            supers = supers[1:]

class Component(Initialisable, Parameterisable):
    def __init__(self, *args, **kwargs):
        self._logger = None
        self._name = None
        
        self.__component_args = list(args)
        self.__component_kwargs = dict(kwargs)
               
        self.__input_description = None
        self.__output_description = None
        
        #Run mixin init methods if this is the first superclass 
        #and there are others after it
        self._perform_init(Component, *args, **kwargs)
        
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
        
        self.logger.debug("Processing stashed args and parameters")
        
        #Process named arguments/parameters
        for parameter in self._get_parameter_hooks():
            kwargs = parameter.consume(self._parameters, **kwargs)     
        #Process positional arguments
        for argument in self._get_argument_hooks():
            args = argument.consume(self._arguments, *args)

        self.logger.info("Processed stashed args and parameters: args=%s, params=%s", self.args.as_list, self.params.as_dict)
        
        #Call the standard initialise method
        self.logger.info("Initialising")
        result = self.initialise(*args, **kwargs)
        
        if not result == False:
            ### TODO: Replace with Initialisable._perform_initialise
            #Call mixin initialise methods
            self._perform_initialise(Component, *args, **kwargs)
        else:
            self.logger.info("Initialisation returned False")
    
    def initialise(self, *args, **kwargs):
        return

    def start(self): return
    def stop(self): return

    @property
    def name(self): return self._name
    
    def set_name(self, name): self._name = name
    
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
    def logger(self):
        if not self._logger:
            self._logger = log.for_component(self) 
        return self._logger
    
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
        
    
    def _set_input_description(self, d):
        self.__input_description = d
    def _set_output_description(self, d):
        self.__output_description = d
        
    @classmethod
    def get_source(cls):
        import inspect
        return inspect.getsource(cls)
        
    @classmethod
    def get_docstring(cls):
        import inspect
        docstring = inspect.getdoc(cls)
        if docstring: docstring = inspect.cleandoc(docstring)
        return docstring
    




