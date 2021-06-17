from . import sources, operators, sinks

def load():
    from actuator import package
    pkg = package.Package('var')
    
    pkg.sources.register_item(None, sources.Get)
    pkg.operators.register_item('set', operators.Set)
    pkg.sinks.register_item(None, sinks.Set)
        
    return pkg
