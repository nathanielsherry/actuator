
class Scope:
    def __init__(self, parent):
        self._values = {}
        self._parent = parent

    @property
    def parent(self): return self._parent

    def has_local(self, key): return key in self._values.keys()
    def has(self, key): return self.has_local(key) or (self.parent.has(key) if self.parent else False)
    def get_local(self, key): return self._values[key]
    def get(self, key): 
        if self.has_local(key): return self.get_local(key)
        if self.parent and self.parent.has(key): return self.parent.get(key)
        raise Exception("Undefined: '%s'" % key)
    def set(self, key, value, claim=False):
        if claim and not self.claim(key, initial=value):
            raise Exception("Claim failed for key {}".format(key))
        self._values[key] = value
    def claim(self, key, initial=None):
        if not self.has_local(key):
            self.set(key, initial, claim=False)
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
        
    def has_local(self, key):
        keys = self.parse(key)
        head = keys[0]
        tail = keys[1:]
        
        if len(keys) > 1:
            #Get the first item in this key chain and make sure it's 
            #a Scope so we can traverse into it w/ remaining keys
            if not super().has_local(head): return False
            scope = super().get_local(head)
            if not isinstance(scope, NamespacedScope): return False
            return scope.has_local(tail)
        elif len(keys) == 1:
            return super().has_local(head)
        else:
            return False
        
    def get_local(self, key):
        if not self.has_local(key):
            raise Exception("Undefined: '%s'" % key) 
        keys = self.parse(key)
        head = keys[0]
        tail = keys[1:]
        
        if len(keys) > 1:
            scope = super().get_local(head)
            return scope.get_local(tail)
        elif len(keys) == 1:
            return super().get_local(head)
        else:
            raise Exception("Undefined: '%s'" % key)
            
    def set(self, key, value, claim=False):
        keys = self.parse(key)
        head = keys[0]
        tail = keys[1:]
        
        if len(keys) > 1:
            if not super().has_local(head):
                raise Exception("Undefined: {}".format(head))
            scope = super().get_local(head)
            scope.set(tail, value, claim)
        elif len(keys) == 1:
            super().set(head, value, claim)
        else:
            raise Exception("Undefined: '%s'" % key)
