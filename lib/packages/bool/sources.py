from actuator.components import source

class TrueSource(source.Source):
    """    
    :output: True
    :outtype: bool
    """
    @property
    def value(self):
        return True
    
class FalseSource(source.Source):
    """    
    :output: False
    :outtype: bool
    """
    @property
    def value(self):
        return False
