from . import sources, operators

def load():
    from actuator import package
    pkg = package.Package('bool')

    pkg.sources.register_item('true', sources.true)
    pkg.sources.register_item('false', sources.false)
    
    pkg.operators.register_item(None, operators.boolean)
    pkg.operators.register_item('not', operators.negation)
    pkg.operators.register_item('all', operators.All)
    pkg.operators.register_item('any', operators.Any)
    pkg.operators.register_item('smooth', operators.Smooth)

    return pkg
