

def get_url(url):
    import requests
    result = requests.get(url)
    rc = result.status_code
    if rc != 200:
        raise Exception("Received status {}".format(rc))
    return result.text

def parse_bool(s):
    if isinstance(s, bool): return s
    if s.lower() in ['true', 'yes', 'on']: return True
    if s.lower() in ['false', 'no', 'off']: return False
    raise Exception("Could not parse {} as boolean".format(s))

def short_string(s, length=30):
    s = str(s)
    s = s.replace("\n", " ")
    if len(s) >= length:
        s = s[:length-3] + "..."
    return s

    
    
__shutdown_hooks = []
def add_shutdown_hook(hook):
    global __shutdown_hooks
    __shutdown_hooks.append(hook)
    
def run_shutdown_hooks():
    for hook in __shutdown_hooks:
        hook()
        
__globals = {}
def set_global(k, v):
    global __globals
    __globals[k] = v
    
def get_global(k, default=None):
    return __globals.get(k, default)
