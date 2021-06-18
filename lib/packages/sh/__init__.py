from . import sources, sinks

def load():
    from actuator import package
    pkg = package.Package('sh')
    pkg.sources.register_item(None, sources.ShellSource)
    pkg.sources.register_item('stdin', sources.StdinSource)
    pkg.sources.register_item('jsonin', sources.JsonSource)
    pkg.sources.register_item('null', sources.NullSource)
    #pkg.sinks.register_item(None, sinks.ShellRunner)
    pkg.sinks.register_item(None, sinks.Shell)
    pkg.sinks.register_item('stdout', sinks.Stdout)
    pkg.sinks.register_item('null', sinks.Null)
    pkg.sinks.register_item('stdout-if', sinks.StdoutIf)
    pkg.sinks.register_item('stdout-msg', sinks.StdoutMsg)
    pkg.sinks.register_item('jsonout', sinks.JsonSink)
    pkg.sinks.register_item('curses', sinks.Curses)
    return pkg
