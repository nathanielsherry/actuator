
class Component:
    def __init__(self, config):
        #Run mixin init methods if this is the first superclass 
        #and there are others after it
        supers = self.__class__.mro()
        supers = supers[supers.index(Component)+1:]
        while True:
            if supers[0] == object: break
            supers[0].__init__(self, config)
            supers = supers[1:]
        
        self._context = None
            
    @property
    def name(self): 
        return type(self).__name__
    
    def __repr__(self):
        return "<{name}>".format(name=self.name)
    def __str__(self):
        return self.name
    
    @property
    def context(self): return self._context
    
    def set_context(self, context):
        self._context = context
    
    @property
    def description_data(self):
        return self.name

    @property
    def description(self):
        import yaml
        return yaml.dump(self.description_data)
