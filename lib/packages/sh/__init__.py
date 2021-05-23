from . import sources, sinks

def load():
    from actuator import package
    pkg = package.Package('sh')
    pkg.sources.register_item(None, sources.ShellSource)
    pkg.sinks.register_item(None, sinks.ShellRunner)
    pkg.sinks.register_item('curses', sinks.Curses)
    return pkg
