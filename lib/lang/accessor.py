from actuator import log

def extract(o, key, _default=None):
    import six
    
    if key == None: return o
    
    #Integer extractors cause the target object to be treated as a list
    if isinstance(key, int): 
        try:
            return o[key]
        except:
            log.error("Index '%s' out of range for list '%s'\n" % (key, o))
            raise
    
    if isinstance(key, six.string_types) and hasattr(o, key): return getattr(o, key)
    if isinstance(o, dict) and key in o: return o[key]
    if isinstance(key, six.string_types) and hasattr(o, "__dict__") and hasattr(o.__dict__, key): return o.__dict__.get(key)
    if callable(key): return key(o)
    if hasattr(o, "__getitem__") and key in o: return o[key]
    return _default

def extractor(key, default=None):
    if isinstance(key, tuple):
        return lambda o: tuple(map(lambda k: extract(o, k, default), key))
    else:
        return lambda o: extract(o, key, default)


#Given a list of dicts, filters the list by key == value
def dicts_filter(dicts, key, value):
    return [d for d in dicts if str(extract(d, key, None)) == value]

def dicts_filterer(key, value):
    return lambda dicts: dicts_filter(dicts, key, value)
    

def compose(*args):
    args = reversed(args)
    args = [arg if callable(arg) else extractor(arg) for arg in args]
    def _compose(f, g):
        return lambda *args, **kwargs: f(g(*args, **kwargs))
    from functools import reduce
    return reduce(_compose, args)
    
def accessor(access_elements):
    if isinstance(access_elements, str):
        strings = access_elements.split(".")
    elif isinstance(access_elements, (list, tuple)):
        strings = access_elements[:]
    else:
        raise Exception("Unknown input format")
    
    components = []
    for s in strings:
        if isinstance(s, int):
            components.append(s)
        elif isinstance(s, list):
            if len(s) == 1:
                components.append(mapper(s[0]))
            elif len(s) == 2:
                key, value = s
                components.append(dicts_filterer(key, value))
            else:
                raise Exception("List accessor elements must have one or two items")
        elif isinstance(s, str):
            components.append(s)

    return compose(*components)

def access(obj, access_elements):
    return accessor(access_elements)(obj)
 
def listmap(fn, lst):
    return list(map(fn, lst))

def mapper(fn):
    from functools import partial
    if not callable(fn) and not fn == None:
        fn = extractor(fn)
    return partial(listmap, fn) 
    
    
from pyparsing import Or, Suppress, ZeroOrMore
from actuator.lang import symbols, values
from actuator.lang.construct import PackageConstruct, ParametersConstruct, ComponentBlueprint

PS_ACCESSOR_ELEMENT = Or([
    values.PS_IDENTIFIER,
    values.PS_INT,
])

PS_ACCESSOR_COLLECTION = (
    Suppress('[') + 
    Or([
        #Map
        PS_ACCESSOR_ELEMENT,
        #Filter
        PS_ACCESSOR_ELEMENT + Suppress('=') + values.PS_PRIMITIVE
    ]) + 
    Suppress(']')
).setParseAction(
    lambda ts: [list(ts)]
)

PS_ACCESSOR_COMPONENT = Or([
    PS_ACCESSOR_ELEMENT,
    PS_ACCESSOR_COLLECTION
])

PS_ACCESSOR = (
    Suppress(symbols.GETSTART) +
    PS_ACCESSOR_COMPONENT + 
    ZeroOrMore(
        Suppress(symbols.IDSEP) + 
        PS_ACCESSOR_COMPONENT
    )
).setParseAction(
    lambda ts: list(ts)
)
