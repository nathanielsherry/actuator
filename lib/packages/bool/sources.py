from actuator import source

class TrueSource(source.Source):
    def __init__(self, config):
        super().__init__(config)
        
    @property
    def value(self):
        return True
    
class FalseSource(source.Source):
    def __init__(self, config):
        super().__init__(config)
        
    @property
    def value(self):
        return False
