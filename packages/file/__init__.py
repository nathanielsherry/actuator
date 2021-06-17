from . import sources, sinks

def load():
    from actuator import package
    pkg = package.Package('file')

    pkg.sources.register_item(None, sources.FileSource)
    
    pkg.sinks.register_item(None, sinks.FileSink)
    
    return pkg
