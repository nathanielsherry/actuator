from actuator.components.operator import Operator
from actuator import util

from actuator.components.decorators import parameter, argument, input, output, allarguments, operator


def tobool(o):
    if isinstance(o, bool): return o
    if isinstance(o, str): return util.parse_bool(o)
    #If it's not a bool or a string, fall back on python's truthy/falsey value
    if o:
        return True
    else:
        return False


@input('any', 'Any payload')
@output('bool', 'Truthy value of the payload')
@operator
def boolean(payload):
    """  
    Converts the payload to its own truthy value.
    """
    return True if payload else False
    

@input('any', 'Any payload')
@output('bool', 'Negation of the truthy value of the payload')
@operator
def negation(payload):
    """  
    Negates the truthy value of the payload, returning a boolean value
    """
    return not payload

    

@input('list', 'Any list of values')
@output('bool', 'True if any values in the list are truthy, False otherwise.')
class Any(Operator):
    """    
    Accepts a list of items and returns true if any items in the list
    evaluate to truthy. This is a wrapper around Python's builtin 'all' function.
    """
    @property
    def value(self):
        value = self.upstream.value
        if not isinstance(value, (list, tuple)):
            value = list(value)
        return any(value)

@input('list', 'Any list of values')
@output('bool', 'True if all values in the list are truthy, False otherwise.')
class All(Operator):
    """    
    Accepts a list of items and returns true if-and-only-if all items in the list
    evaluate to truthy. This is a wrapper around Python's builtin 'all' function.
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
class Smooth(Operator):
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
    
