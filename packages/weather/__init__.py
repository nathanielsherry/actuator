from . import sources

def load():
    from actuator import package
    pkg = package.Package('weather')
    
    pkg.sources.register_item(None, sources.Fetch)
    pkg.sources.register_item('below', sources.Below)
    pkg.sources.register_item('above', sources.Above)
    
    return pkg
