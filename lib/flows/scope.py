from threading import Lock, Condition


class Scope:
    def __init__(self, parent, owner):
        self._values = {}
        self._parent = parent
        self._owner = owner

        self._claim_lock = Condition(Lock())
        
        #Set up relative scope protected name(s)
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
    
    def get_local(self, key, domain=None, blocking=True):
        while blocking:
            if self.has_local(key, domain): 
                break
            with self._claim_lock:
                self._claim_lock.wait()
                
        return self.domain(domain)[key]
    
    def get(self, key, domain=None, blocking=True):
        #Because 'get' can either fetch a value locally or viaa parent scope as 
        #a fallback, we take them in order, but only once at least one is 
        #available. This means that on startup there will be a possibility that
        #a parent value that will *eventually* be shadowed by a local one might
        #be first available and therefore fetched on startup 
        while blocking:
            if self.has(key, domain):
                break
            with self._claim_lock:
                self._claim_lock.wait()
        
        #Local scope is more tightly bound
        if self.has_local(key, domain): return self.get_local(key, domain, blocking)
        #Parent scopes as fallbacks in order of proximity
        if self.parent and self.parent.has(key, domain): return self.parent.get(key, domain, blocking)
        
        errmsg = "Undefined: '{}'".format(key)
        if domain:
            errmsg += " from domain {}".format(domain)
        raise Exception(errmsg)
        
    def set(self, key, value, domain=None, claim=False):
        if claim:
            #The claim method ultimately just calls the set method again
            #with claim=False if the claim succeedes. This means that we don't
            #have to do anything on success here. It also means we only have 
            #code to set the variable in one spot -- the set method. 
            if not self.claim(key, initial=value, domain=domain):
                errmsg = "Claim failed for key {}".format(key)
                if domain:
                    errmsg += " in domain {}".format(domain)
                raise Exception(errmsg)
        else:
            self.domain(domain)[key] = value
            
    def claim(self, key, initial=None, domain=None,):
        
        #If it has already been set, return false
        if not self.has_local(key, domain):
            
            #Acquire an exclusive lock to claim a new viariable. It is important 
            #that we do this *before* testing if it has already been claimed, 
            #since we don't want two threads both deciding that the key is free,
            #and then both trying to claim it. BUT, we also don't want unneeded
            #locking, which can be slow. So we test, lock, and test again.
            with self._claim_lock:
            
                if not self.has_local(key, domain):
                    self.set(key, initial, domain=domain, claim=False)
                    #Any blocking 'get' calls can check if they have what they need now
                    self._claim_lock.notify_all()
                    result = True
                else:
                    result = False   
                            
        else:
            result = False
        
        return result
        
    

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
        head, tail = keys[0], keys[1:]
        
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
        
    def get_local(self, key, domain=None, blocking=True):
        if not self.has_local(key, domain):
            raise Exception("Undefined: '%s'" % key) 
        keys = self.parse(key)
        head, tail = keys[0], keys[1:]
        
        if len(keys) > 1:
            scope = super().get_local(head, domain, blocking)
            return scope.get_local(tail, domain, blocking)
        elif len(keys) == 1:
            return super().get_local(head, domain, blocking)
        else:
            raise Exception("Undefined: '%s'" % key)
            
    def set(self, key, value, domain=None, claim=False):
        keys = self.parse(key)
        head, tail = keys[0], keys[1:]
        
        
        if len(keys) > 1:
            if not super().has_local(head, domain):
                raise Exception("Undefined: {}".format(head))
            scope = super().get_local(head, domain)
            scope.set(tail, value, domain=domain, claim=claim)
        elif len(keys) == 1:
            super().set(head, value, domain=domain, claim=claim)
        else:
            raise Exception("Undefined: '%s'" % key)
