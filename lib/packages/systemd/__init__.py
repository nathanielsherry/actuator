from . import sinks, sources

def load():
    from actuator import package
    pkg = package.Package('systemd')
    
    pkg.sources.register_item(None, sources.Info)
    pkg.sources.register_item('state', sources.State)
    pkg.sources.register_item('active', sources.Active)
    
    pkg.sinks.register_item('toggle', sinks.Toggle)

    return pkg
