

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
