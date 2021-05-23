#!/usr/bin/python3

SEP = "."

#Generic class for storing namespaced key value items
#This class should be used/composed rather than extended
class Archive():
    def __init__(self, name):
        self._items = {}
        self._name = name
    
    @property
    def name(self): return self._name
    
    @property
    def contents(self): return dict(self._items)

    def get(self, name):
        #name = self.expand(name)
        return self._items.get(name, None)

    def register_item(self, name, item):
        #name = self.expand(name)
        if name in self._items:
            raise Exception("Item with name {} is already registered".format(name))
        self._items[name] = item

    #def expand(self, name):
    #    if name and self.name:
    #        if name.startswith(self.name + SEP): 
    #            return name
    #        return self.name + SEP + name
    #    elif name: return name
    #    elif self.name: return self.name
    #    else: return None            



#Stores a collection of related sources and sinks
class Package:
    def __init__(self, name):
        self._name = name
        self._sources = Archive(name)
        self._sinks = Archive(name)
        self._monitors = Archive(name)
    
    @property
    def name(self): return self._name
    
    @property
    def sources(self): return self._sources
    
    @property
    def sinks(self): return self._sinks
    
    @property
    def monitors(self): return self._monitors
        


#Provides a single, coherent view into the entire package system via namespaces
class Registry:
    def __init__(self):
        pass
    
    def load_package(self, name):
        package = None
        for loader in loaders:
            package = loader.load(name)
            if package: break
        if not package:
            raise Exception("")
        self.packages.register_item(name, package)
    
    @property
    def source_names(self):
        return self.item_names(lambda p: p.sources)

    @property
    def sink_names(self):
        return self.item_names(lambda p: p.sinks)
    
    @property
    def monitor_names(self):
       return self.item_names(lambda p: p.monitors)

    def item_names(self, get_archive):
        names = [] 
        for loader in loaders:
            for packagename, package in loader.packages.contents.items():
                for itemname, item in get_archive(package).contents.items():
                    name = ""
                    if packagename: name += packagename
                    if packagename and itemname: name += SEP
                    if itemname: name += itemname
                    names.append(name)
        return names


    def lookup_item(self, name, get_archive):
        if not SEP in name:
            #This could be one of two things. This could be a packageless 
            #builtin or this could be a default item in a package. We
            #try to resolve the packageless builtin first
            
            #Try to find this as a built-in
            for loader in loaders:
                package = loader.packages.get(None)
                if package:
                    source = get_archive(package).get(name)
                    if source: return source
                    
            #Then try to find a matching package with a default item
            for loader in loaders:
                package = loader.packages.get(name)
                if package:
                    source = get_archive(package).get(None)
                    if source: return source
                    
        else:
            pkgname, itemname = name.split(SEP)
            for loader in loaders:
                package = loader.packages.get(pkgname)
                if package:
                    source = get_archive(package).get(itemname)
                    if source: return source
                
    def lookup_source(self, name):
        return self.lookup_item(name, lambda p: p.sources)
    
    def lookup_sink(self, name):
        return self.lookup_item(name, lambda p: p.sinks)
        
    def lookup_monitor(self, name):
        return self.lookup_item(name, lambda p: p.monitors)
        
        
    def build_item(self, name, config, get_archive):
        item = self.lookup_item(name, get_archive)
        return item(config)
        
        
    def build_source(self, name, config):
        return self.build_item(name, config, lambda p: p.sources)
        
    def build_sink(self, name, config):
        return self.build_item(name, config, lambda p: p.sinks)
        
    def build_monitor(self, name, config):
        return self.build_item(name, config, lambda p: p.monitors)
        
        

#Generic class for loading packages from a source
class Loader:
    def __init__(self):
        self._packages = Archive(None)
        self.scan()
    
    @property
    def packages(self): return self._packages
    
    def scan(self): raise Exception("Unimplemented")
    
    #Loads a package with a specific name into the 
    def load(self, name): raise Exception("Unimplemented")
    
    
class DirLoader(Loader):
    def __init__(self, name, path):
        self._name = name
    
    def load(self, name):
        import importlib
        try:
            m = importlib.__import__("actuator.packages.{}.{}".format(self._name, name))
            return m.load()
        except:
            return None


class BuiltinLoader(Loader):
    
    def scan(self): raise Exception("Unimplemented")
    
    def load(self, name):
        import importlib
        try:
            m = importlib.__import__("actuator.packages.{}".format(name))
            return m.load()
        except:
            return None

class HardCodedLoader(Loader):
    def scan(self):
        from actuator.packages import net
        p = net.load()
        self.packages.register_item(p.name, p)
        
        from actuator.packages import sh
        p = sh.load()
        self.packages.register_item(p.name, p)
        
class LegacyLoader(Loader):
    def scan(self):
        p = Package(None)
        
        from actuator import sink as mod_sink
        for k, v in mod_sink.instructions().items():
            p.sinks.register_item(k, v)
        
        from actuator import source as mod_source
        for k, v in mod_source.instructions().items():
            p.sources.register_item(k, v)
            
        from actuator import monitor as mod_monitor
        for k, v in mod_monitor.instructions().items():
            p.monitors.register_item(k, v)
        
        self.packages.register_item(p.name, p)
    
loaders = [HardCodedLoader(), LegacyLoader()]

REGISTRY = Registry()

if __name__ == "__main__":
    print(REGISTRY.source_names)
    print(REGISTRY.sink_names)
    print(REGISTRY.lookup_source('net.url'))
    print(REGISTRY.lookup_sink('print'))
