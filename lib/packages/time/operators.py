from actuator.components import operator

class IntervalSource(operator.Operator):
    def initialise(self, *args, **kwargs):
        super().initialise(*args, **kwargs)
        self._sleep_interval = float(kwargs.get('sleep', '1'))
    
    def sleep(self):
        import time
        time.sleep(self._sleep_interval)
    
    @property
    def value(self):
        import time
        self.sleep()
        return self.upstream.value
