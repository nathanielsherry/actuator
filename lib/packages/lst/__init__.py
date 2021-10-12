from . import operators

def load():
    from actuator import package
    pkg = package.Package('lst')
    pkg.operators.register_item('head', operators.head)
    pkg.operators.register_item('tail', operators.tail)
    pkg.operators.register_item('last', operators.last)
    pkg.operators.register_item('init', operators.init)
    pkg.operators.register_item('slice', operators.slice)
    pkg.operators.register_item('len', operators.length)
    pkg.operators.register_item('reverse', operators.reverse)
    pkg.operators.register_item('join', operators.join)
    pkg.operators.register_item('sum', operators.lst_sum)
    pkg.operators.register_item('avg', operators.avg)
    pkg.operators.register_item('product', operators.product)
    pkg.operators.register_item('max', operators.lst_max)
    pkg.operators.register_item('min', operators.lst_min)
    pkg.operators.register_item('repeat', operators.repeat)
    pkg.operators.register_item('ints', operators.ints)
    pkg.operators.register_item('floats', operators.floats)
    return pkg
