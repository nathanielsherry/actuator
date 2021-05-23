from . import sources

def load():
    from actuator import package
    pkg = package.Package('time')
    pkg.sources.register_item(None, sources.TimeSource)
    pkg.sources.register_item('epoch', sources.EpochSource)
    pkg.sources.register_item('during', sources.DuringSource)
    return pkg
