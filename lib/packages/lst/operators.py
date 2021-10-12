from actuator import util
from actuator.components.operator import Operator 

from actuator.components.decorators import parameter, argument, input, output, allarguments, operator

@operator
def head(payload): return payload[0]   

@operator
def tail(payload): return payload[1:]

@operator
def last(payload): return payload[-1]

@operator
def init(payload): return payload[:-2]   

#def argument(name, ptype, default=None, desc=None, parser=None):
@argument('start', 'int', 0, 'Starting index for slice. Inclusive')
@argument('end', 'int', -1, 'Ending index for slice. Exclusive')
@operator
def slice(payload, start=0, end=-1):
    return payload[start:end]

@operator
def length(payload): return len(payload)

@operator
def reverse(payload):
    payload = payload[:]
    payload.reverse()
    return payload

@parameter('delim', 'str', ', ', 'Delimiter to join with')
@operator
def join(payload, delim=', '): return delim.join(payload)

@operator
def lst_sum(payload): return sum(payload)

@operator
def avg(payload): return float(sum(payload))/float(len(payload))


@operator
def product(payload):
    p = 1
    for v in payload:
        p *= v
    return p

@operator
def lst_max(payload): return max(payload)

@operator
def lst_min(payload): return min(payload)


@argument('count', 'int', 1, 'Number of repetitions', parser=int)
@operator
def repeat(payload, count=1): return [payload for i in range(0, count)]
            

#TODO: nice if there were a more generic way to map a function over a list
@operator
def ints(upstream): return [int(s) for s in upstream]
    
@operator
def floats(upstream): return [float(s) for s in upstream]
