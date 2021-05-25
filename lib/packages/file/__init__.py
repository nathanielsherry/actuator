from . import sources

def load():
    from actuator import package
    pkg = package.Package('file')

    pkg.sources.register_item(None, sources.FileSource)
    
    return pkg
