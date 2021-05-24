from actuator import operator

class IntervalSource(operator.Operator):
    def __init__(self, config):
        super().__init__(config)
        self._sleep_interval = float(config.get('sleep', '1'))
    
    def sleep(self):
        import time
        time.sleep(self._sleep_interval)
    
    @property
    def value(self):
        import time
        self.sleep()
        return self.upstream.value
