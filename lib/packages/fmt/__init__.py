from . import sources

def load():
    from actuator import package
    pkg = package.Package('fmt')
    pkg.sources.register_item('tojson', sources.ToJson)
    pkg.sources.register_item('fromjson', sources.FromJson)
    pkg.sources.register_item('toyaml', sources.ToYaml)
    pkg.sources.register_item('fromyaml', sources.FromYaml)
    #pkg.sinks.register_item('serve', sinks.WebServerSink)
    return pkg
