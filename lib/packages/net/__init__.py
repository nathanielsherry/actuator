from . import sources, sinks

def load():
    from actuator import package
    pkg = package.Package('net')
    pkg.sources.register_item('url', sources.URLSource)
    pkg.sources.register_item('pingable', sources.Pingable)
    pkg.sinks.register_item('serve', sinks.WebServerSink)
    return pkg
