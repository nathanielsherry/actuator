from actuator.components import operator
from actuator import util

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
