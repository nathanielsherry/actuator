from actuator.components import operator
from actuator import util

from actuator.components.decorators import parameter, argument, input, output, allarguments


def tobool(o):
    if isinstance(o, bool): return o
    if isinstance(o, str): return util.parse_bool(o)
    #If it's not a bool or a string, fall back on python's truthy/falsey value
    if o:
        return True
    else:
        return False

class Not(operator.Operator):
    """  
    :input: A value which can be interpereted as a boolean
    :intype: bool, str
    
    :output: The opposite boolean value
    :outtype: bool
    """
    @property
    def value(self):
        value = tobool(self.upstream.value)
        return not value
    
    
class Any(operator.Operator):
    """    
    :input: List of values
    :intype: list
    
    :output: True if any value in the list is truthy, False otherwise.
    :outtype: bool
    """
    @property
    def value(self):
        value = self.upstream.value
        if not isinstance(value, (list, tuple)):
            value = list(value)
        return any(value)
        
class All(operator.Operator):
    """    
    :input: List of values
    :intype: list
    
    :output: True if all values in the list are truthy, False otherwise.
    :outtype: bool
    """
    @property
    def value(self):
        value = self.upstream.value
        if not isinstance(value, (list, tuple)):
            value = list(value)
        return all(value)
        


#Eliminates jitter from a value flapping a bit. The state starts as False and
#will switch when consistently the opposite for `delay[state]` seconds.
#delay is a dict with integer values for keys True and False
@parameter('delay', 'int', 10, 'Seconds to delay before switching states')
@parameter('fast_false', 'boolean', False, 'Flip to False immediately')
@parameter('fast_true', 'boolean', False, 'Flip to True immediately')
class Smooth(operator.Operator):
    def initialise(self, *args, **kwargs):        
        import time    
        self._last_time = time.time()
        self._last = False
        self._state = False

    def delay_for(self, newstate):
        if newstate == True: 
            return 0 if self.params.fast_true else self.params.delay
        else:
            return 0 if self.params.fast_false else self.params.delay

    @property
    def value(self):
        import time
        
        #get the result from the wrapped state
        new_result = self.upstream.value
        
        if new_result != self._last:
            #reset the last change time last known status
            self._last_time = time.time()
            self._last = new_result
        
        #If the state doesn't match the last `delay` seconds, flip it
        time_delta = time.time() - self._last_time
        differs = self._state != self._last
        delay = self.delay_for(self._last)
        stale = delay >= time_delta
        if differs and stale:
            self._state = self._last
            
        return self._state
    
