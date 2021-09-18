from . import sources, operators

def load():
    from actuator import package
    pkg = package.Package('time')
    
    pkg.sources.register_item(None, sources.NowSource)
    pkg.sources.register_item('stamp', sources.TimestampSource)
    pkg.sources.register_item('epoch', sources.EpochSource)
    pkg.sources.register_item('during', sources.DuringSource)
    
    pkg.operators.register_item('interval', operators.IntervalSource)
    
    return pkg
