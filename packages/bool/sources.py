from actuator.components import source

class TrueSource(source.Source):
    @property
    def value(self):
        return True
    
class FalseSource(source.Source):
    @property
    def value(self):
        return False
