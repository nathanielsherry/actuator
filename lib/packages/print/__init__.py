from . import sinks

def load():
    from actuator import package
    pkg = package.Package('print')
    pkg.sinks.register_item(None, sinks.Print)
    pkg.sinks.register_item('if', sinks.PrintIf)
    pkg.sinks.register_item('msg', sinks.PrintMsg)
    return pkg
