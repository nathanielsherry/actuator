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
    
def accessor(access_string):
    strings = access_string.split(".")
    
    components = []
    for s in strings:
        if s.isnumeric():
            components.append(int(s))
        elif s[0] == '[' and s[-1] == ']':
            s = s[1:-1]
            if '=' in s:
                key, value = s.split('=', maxsplit=1)
                components.append(dicts_filterer(key, value))
            else:    
                components.append(mapper(s))
        else:
            components.append(s)

    return compose(*components)

def access(obj, access_string):
    return accessor(access_string)(obj)
 
def listmap(fn, lst):
    return list(map(fn, lst))

def mapper(fn):
    from functools import partial
    if not callable(fn) and not fn == None: 
        fn = extractor(fn)
    return partial(listmap, fn) 
