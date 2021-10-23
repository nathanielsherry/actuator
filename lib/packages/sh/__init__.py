from . import sources, sinks

def load():
    from actuator import package
    pkg = package.Package('sh')
    pkg.sources.register_item(None, sources.ShellSource)
    pkg.sources.register_item('stdin', sources.stdin)
    #pkg.sinks.register_item(None, sinks.ShellRunner)
    pkg.sinks.register_item(None, sinks.Shell)
    pkg.sinks.register_item('stdout', sinks.stdout)
    pkg.sinks.register_item('print-if', sinks.stdout_print_if)
    pkg.sinks.register_item('print', sinks.stdout_print)
    pkg.sinks.register_item('curses', sinks.Curses)
    return pkg
