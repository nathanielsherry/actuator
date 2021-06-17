from . import operators

def load():
    from actuator import package
    pkg = package.Package('lst')
    pkg.operators.register_item('head', operators.Head)
    pkg.operators.register_item('tail', operators.Tail)
    pkg.operators.register_item('last', operators.Last)
    pkg.operators.register_item('init', operators.Init)
    pkg.operators.register_item('slice', operators.Slice)
    pkg.operators.register_item('len', operators.Length)
    pkg.operators.register_item('reverse', operators.Reverse)
    pkg.operators.register_item('join', operators.Join)
    pkg.operators.register_item('sum', operators.Sum)
    pkg.operators.register_item('avg', operators.Avg)
    pkg.operators.register_item('prod', operators.Prod)
    pkg.operators.register_item('max', operators.Max)
    pkg.operators.register_item('min', operators.Min)
    pkg.operators.register_item('replicate', operators.Min)
    pkg.operators.register_item('ints', operators.Ints)
    pkg.operators.register_item('floats', operators.Floats)
    return pkg
