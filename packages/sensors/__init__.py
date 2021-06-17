from .sources.temper import sources as temper

def load():
    from actuator import package
    pkg = package.Package('sensors')
    
    pkg.sources.register_item('temper', temper.Temper)

    return pkg
