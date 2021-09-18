from actuator.components import operator

from actuator.components.decorators import parameter, argument, input, output, allarguments


@parameter('sleep', 'int', 1, 'Length of interval in seconds')
class IntervalSource(operator.Operator):   
    """
    Sleep for a given interval before returning the upstream payload.
    """  
    @property
    def value(self):
        import time
        time.sleep(self.params.sleep)
        return self.upstream.value
