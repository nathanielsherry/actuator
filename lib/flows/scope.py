
class Scope:
    def __init__(self, parent, owner):
        self._values = {}
        self._parent = parent
        self._owner = owner
        
        self.set('parent', self.parent, claim=True)

    @property
    def parent(self): return self._parent

    @property
    def owner(self): return self._owner

    @property
    def root(self):
        if self.parent: return self.parent.root
        return self

    def domain(self, domain):
        if not domain in self._values:
            self._values[domain] = {}
        return self._values[domain]

    def has_local(self, key, domain=None): return key in self.domain(domain).keys()
    def has(self, key, domain=None): return self.has_local(key, domain) or (self.parent.has(key, domain) if self.parent else False)
    def get_local(self, key, domain=None): return self.domain(domain)[key]
    def get(self, key, domain=None): 
        if self.has_local(key, domain): return self.get_local(key, domain)
        if self.parent and self.parent.has(key, domain): return self.parent.get(key, domain)
        errmsg = "Undefined: '{}'".format(key)
        if domain:
            errmsg += " from domain {}".format(domain)
        raise Exception(errstd)
    def set(self, key, value, domain=None, claim=False):
        if claim and not self.claim(key, initial=value, domain=domain):
            errmsg = "Claim failed for key {}".format(key)
            if domain:
                errmsg += " in domain {}".format(domain)
            raise Exception(errmsg)
        self.domain(domain)[key] = value
    def claim(self, key, initial=None, domain=None,):
        if not self.has_local(key, domain):
            self.set(key, initial, domain=domain, claim=False)
            return True
        else:
            return False
    

class NamespacedScope(Scope):
    def parse(self, key):
        if isinstance(key, str): 
            return key.split(".")
        elif isinstance(key, (list, tuple)):
            return key
        else:
            raise Exception("Unrecognised Key {}".format(key))
        
    def has_local(self, key, domain=None):
        keys = self.parse(key)
        head = keys[0]
        tail = keys[1:]
        
        if len(keys) > 1:
            #Get the first item in this key chain and make sure it's 
            #a Scope so we can traverse into it w/ remaining keys
            if not super().has_local(head, domain): return False
            scope = super().get_local(head, domain)
            if not isinstance(scope, NamespacedScope): return False
            return scope.has_local(tail, domain)
        elif len(keys) == 1:
            return super().has_local(head, domain)
        else:
            return False
        
    def get_local(self, key, domain=None):
        if not self.has_local(key, domain):
            raise Exception("Undefined: '%s'" % key) 
        keys = self.parse(key)
        head = keys[0]
        tail = keys[1:]
        
        if len(keys) > 1:
            scope = super().get_local(head, domain)
            return scope.get_local(tail, domain)
        elif len(keys) == 1:
            return super().get_local(head, domain)
        else:
            raise Exception("Undefined: '%s'" % key)
            
    def set(self, key, value, domain=None, claim=False):
        keys = self.parse(key)
        head = keys[0]
        tail = keys[1:]
        
        if len(keys) > 1:
            if not super().has_local(head, domain):
                raise Exception("Undefined: {}".format(head))
            scope = super().get_local(head, domain)
            scope.set(tail, value, domain=domain, claim=claim)
        elif len(keys) == 1:
            super().set(head, value, domain=domain, claim=claim)
        else:
            raise Exception("Undefined: '%s'" % key)
