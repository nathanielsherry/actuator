from . import sources

def load():
    from actuator import package
    pkg = package.Package('proc')
    
    pkg.sources.register_item(None, sources.info)
    pkg.sources.register_item('get', sources.get)
    pkg.sources.register_item('has', sources.has)
    pkg.sources.register_item('search', sources.search)
    pkg.sources.register_item('names', sources.names)
    #pkg.sources.register_item('stdin', sources.StdinSource)
    #pkg.sources.register_item('jsonin', sources.JsonSource)
    #pkg.sinks.register_item(None, sinks.ShellRunner)
    #pkg.sinks.register_item(None, sinks.Shell)
    #pkg.sinks.register_item('stdout', sinks.Stdout)
    #pkg.sinks.register_item('null', sinks.Null)
    #pkg.sinks.register_item('stdout-if', sinks.StdoutIf)
    #pkg.sinks.register_item('stdout-msg', sinks.StdoutMsg)
    #pkg.sinks.register_item('jsonout', sinks.JsonSink)
    #pkg.sinks.register_item('curses', sinks.Curses)
    return pkg
