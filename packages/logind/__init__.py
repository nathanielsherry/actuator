from . import sources

def load():
    from actuator import package
    pkg = package.Package('logind')
    
    pkg.sources.register_item(None, sources.Info)
    pkg.sources.register_item('locked', sources.Locked)
        
    return pkg
