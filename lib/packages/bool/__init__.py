from . import sources, operators

def load():
    from actuator import package
    pkg = package.Package('bool')

    pkg.sources.register_item('true', sources.TrueSource)
    pkg.sources.register_item('false', sources.FalseSource)
    
    pkg.operators.register_item('not', operators.Not)
    pkg.operators.register_item('all', operators.All)
    pkg.operators.register_item('any', operators.Any)
    pkg.operators.register_item('smooth', operators.Smooth)

    return pkg
