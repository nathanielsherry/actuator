from actuator import util
from actuator.components import operator


class Head(operator.Operator):
    @property
    def value(self):
        value = self.upstream.value
        return value[0]
    
    
class Tail(operator.Operator):
    @property
    def value(self):
        value = self.upstream.value
        return value[1:]
    
    
class Last(operator.Operator):
    @property
    def value(self):
        value = self.upstream.value
        return value[-1]
    
    
class Init(operator.Operator):
    @property
    def value(self):
        value = self.upstream.value
        return value[:-2]
    
class Slice(operator.Operator):
    def initialise(self, *args, **kwargs):
        super().initialise(*args, **kwargs)
        self._start = args[0]
        self._end = args[1]
        
    @property
    def value(self):
        value = self.upstream.value
        return value[self._start:self._end]
    
    
class Length(operator.Operator):
    @property
    def value(self):
        value = self.upstream.value
        return len(value)
        
class Reverse(operator.Operator):
    @property
    def value(self):
        value = self.upstream.value[:]
        value.reverse()
        return value
    
class Join(operator.Operator):
    def initialise(self, *args, **kwargs):
        super().initialise(*args, **kwargs)
        self._delim = args[0]
        
    @property
    def value(self):
        value = self.upstream.value
        return self._delim.join(value)
        
class Sum(operator.Operator):
    @property
    def value(self):
        value = self.upstream.value
        return sum(value)
        
class Avg(operator.Operator):
    @property
    def value(self):
        value = self.upstream.value
        return float(sum(value))/float(len(value))
        
class Prod(operator.Operator):
    @property
    def value(self):
        value = self.upstream.value
        p = 1
        for v in value:
            p *= v
        return p
    
class Max(operator.Operator):
    @property
    def value(self):
        value = self.upstream.value
        return max(value)
        
class Min(operator.Operator):
    @property
    def value(self):
        value = self.upstream.value
        return min(value)
         
        
class Replicate(operator.Operator):
    def initialise(self, *args, **kwargs):
        super().initialise(*args, **kwargs)
        self._times = int(args[0])
        
    @property
    def value(self):
        value = self.upstream.value
        agg = []
        for i in range(0, self._times):
            agg.append(value)
            

#TODO: nice if there were a more generic way to map a function over a list
class Ints(operator.Operator):
    @property
    def value(self):
        value = self.upstream.value
        return [int(s) for s in value]
    
class Floats(operator.Operator):
    @property
    def value(self):
        value = self.upstream.value
        return [float(s) for s in value]
