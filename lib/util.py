

def twosplit(s, delim):
    parts = s.split(delim, maxsplit=1)
    first = parts[0]
    second = ""
    if len(parts) > 1:
        second = parts[1]
    return first, second

#Reads an arg as comma separated k=v pairs 
def read_args_kv(arg):
    if arg == None: return {}
    params = read_args_list(arg)
    parameters = {}
    for param in params:
        key, value = twosplit(param, "=")
        parameters[key] = value
    return parameters

#Reads an arg as comma separated list 
def read_args_list(arg):
    if arg == None: return []
    return arg.split(",")

def get_url(url):
    import requests
    result = requests.get(url)
    rc = result.status_code
    if rc != 200:
        raise Exception("Received status {}".format(rc))
    return result.text

def parse_bool(s):
    if s.lower() in ['true', 'yes', 'on']: return True
    if s.lower() in ['false', 'no', 'off']: return False
    raise Exception("Could not parse {} as boolean".format(s))

def short_string(s, length=30):
    s = str(s)
    s = s.replace("\n", " ")
    if len(s) >= length:
        s = s[:length-3] + "..."
    return s

class BaseClass:
    
    @property
    def name(self): 
        return type(self).__name__
        
    def __repr__(self):
        return "<{name}>".format(name=self.name)
    def __str__(self):
        return self.name
