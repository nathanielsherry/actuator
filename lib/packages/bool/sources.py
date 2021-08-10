from actuator.components import source

class TrueSource(source.Source):
    """
    Emits a boolean True
    """
    @property
    def value(self):
        return True
    
class FalseSource(source.Source):
    """
    Emits a boolean False
    """
    @property
    def value(self):
        return False
