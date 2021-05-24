from . import sources, operators

def load():
    from actuator import package
    pkg = package.Package('fmt')

    pkg.operators.register_item('tojson', operators.ToJson)
    pkg.operators.register_item('fromjson', operators.FromJson)
    pkg.operators.register_item('toyaml', operators.ToYaml)
    pkg.operators.register_item('fromyaml', operators.FromYaml)

    return pkg
