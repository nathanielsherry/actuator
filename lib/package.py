#!/usr/bin/python3

SEP = "."

from actuator import log
from collections import OrderedDict

#Generic class for storing namespaced key value items
#This class should be used/composed rather than extended
class Archive():
    def __init__(self, name):
        self._items = {}
        self._name = name
    
    @property
    def name(self): return self._name
    
    @property
    def contents(self):
        sorted_keys = sorted(self._items.keys(), key=lambda k: k if k else '') 
        return OrderedDict((key, self._items[key]) for key in sorted_keys)

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
        self._operators = Archive(name)
    
    @property
    def name(self): return self._name
    
    @property
    def sources(self): return self._sources
    
    @property
    def sinks(self): return self._sinks
    
    @property
    def monitors(self): return self._monitors
    
    @property
    def operators(self): return self._operators
        


#Provides a single, coherent view into the entire package system via namespaces
class Registry:
    def __init__(self):
        pass
    
    @property
    def source_names(self):
        return self.item_names(lambda p: p.sources)

    @property
    def sink_names(self):
        return self.item_names(lambda p: p.sinks)
    
    @property
    def monitor_names(self):
       return self.item_names(lambda p: p.monitors)

    @property
    def operator_names(self):
        return self.item_names(lambda p: p.operators)

    def item_names(self, get_archive):
        names = [] 
        for package in self.packages:
            for itemname, item in get_archive(package).contents.items():
                name = ""
                if package.name: name += package.name
                if package.name and itemname: name += SEP
                if itemname: name += itemname
                names.append(name)
        return names

    @property
    def packages(self):
        ps = []
        for loader in loaders:
            for packagename, package in loader.packages.contents.items():
                ps.append(package)
        ps = sorted(ps, key=lambda k: k.name if k and k.name else '')
        return ps
    
    def get_package(self, name):
        for loader in loaders:
            if name in loader.packages.contents:
                return loader.packages.contents[name]
        return None


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
        
    def lookup_operator(self, name):
        return self.lookup_item(name, lambda p: p.operators)
        
    def build_item(self, name, get_archive, *args, **kwargs):
        item = self.lookup_item(name, get_archive)
        component = item(*args, **kwargs)
        component.set_name(name)
        return component
        
        
    def build_source(self, name, *args, **kwargs):
        return self.build_item(name, lambda p: p.sources, *args, **kwargs)
        
    def build_sink(self, name, *args, **kwargs):
        return self.build_item(name, lambda p: p.sinks, *args, **kwargs)
        
    def build_monitor(self, name, *args, **kwargs):
        return self.build_item(name, lambda p: p.monitors, *args, **kwargs)
        
    def build_operator(self, name, *args, **kwargs):
        return self.build_item(name, lambda p: p.operators, *args, **kwargs)
        
        

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
    
    


class LocalPackageLoader(Loader):
    
    def scan(self): 
        import os
        from actuator import packages
        spec = packages.__spec__
        # Earlier versions of python (like 3.6) can't index the 
        # spec.submodule_search_locations directly
        path = list(spec.submodule_search_locations)[0]
        for entry in os.scandir(path):
            if not entry.is_dir(): continue
            try:
                self.load(entry.name)
            except:
                log.warn("Failed to load package " + entry.name)
    
    def load(self, name):
        import importlib
        try:
            m = importlib.import_module("actuator.packages.{}".format(name))
            package = m.load()
            if not package: return
            self.packages.register_item(package.name, package)
        except:
            import traceback
            log.error(traceback.format_exc())
            raise

class BuiltinLoader(Loader):
    def scan(self):
        p = Package(None)
        
        from actuator.components import sink as mod_sink
        for k, v in mod_sink.instructions().items():
            p.sinks.register_item(k, v)
        
        from actuator.components import source as mod_source
        for k, v in mod_source.instructions().items():
            p.sources.register_item(k, v)
            
        from actuator.components import monitor as mod_monitor
        for k, v in mod_monitor.instructions().items():
            p.monitors.register_item(k, v)
            
        from actuator.components import operator as mod_operator
        for k, v in mod_operator.instructions().items():
            p.operators.register_item(k, v)
        
        self.packages.register_item(p.name, p)
    
loaders = [LocalPackageLoader(), BuiltinLoader()]

REGISTRY = Registry()

if __name__ == "__main__":
    print(REGISTRY.source_names)
    print(REGISTRY.sink_names)
    print(REGISTRY.lookup_source('net.url'))
    print(REGISTRY.lookup_sink('print'))
