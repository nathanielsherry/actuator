from actuator import log

from actuator.lang.construct import PackageConstruct, ParametersConstruct, ComponentBlueprint
from actuator.lang import symbols, keywords, values

from pyparsing import srange, Word, Or, And, Suppress, ZeroOrMore, OneOrMore, QuotedString

#####################
# COMPONENT PARSING #
#####################

def build_comp_pkg(ts):
    if len(ts) == 1:
        return PackageConstruct(ts[0], None)
    elif len(ts) == 2:
        return PackageConstruct(ts[0], ts[1])
    else:
        raise Exception("Package name requires either 1 or 2 arguments")
PS_COMP_PKG = Or([
        values.PS_IDENTIFIER,
        values.PS_IDENTIFIER + Suppress(".") + values.PS_IDENTIFIER
]).setParseAction(build_comp_pkg)

PS_COMP_PARAMETER_KEY = values.PS_IDENTIFIER.copy()
PS_COMP_PARAMETER_VALUE = values.PS_VALUE.copy()
PS_COMP_PARAMETER = Or([
    PS_COMP_PARAMETER_KEY + Suppress("=") + PS_COMP_PARAMETER_VALUE,
    PS_COMP_PARAMETER_VALUE
]).setParseAction(
    lambda ts: [ts]
)

def build_comp_parameters(ts):
    args = []
    kwargs = {}
    for p in ts:
        if len(p) == 1:
            args.append(p[0])
        elif len(p) == 2:
            kwargs[p[0]] = p[1]
    return ParametersConstruct(*args, **kwargs)
PS_COMP_PARAMETERS = (
    Suppress("(") + 
    PS_COMP_PARAMETER + 
    ZeroOrMore(Suppress(",") + PS_COMP_PARAMETER) + 
    Suppress(")")
).setParseAction(build_comp_parameters)


def build_comp_expression(ts):
    pkg = ts[0]
    params = ParametersConstruct()
    if len(ts) >= 2:
        params = ts[1]
    return ComponentBlueprint(PackageConstruct(pkg.package, pkg.element), params)
PS_COMP_EXPRESSION = Or([
    PS_COMP_PKG,
    PS_COMP_PKG + PS_COMP_PARAMETERS
]).setParseAction(build_comp_expression)

log.debug("-------------------------------")
log.debug(PS_COMP_PKG.parseString("sh.stdin"))
log.debug(PS_COMP_PARAMETERS.parseString("(split=False)"))
log.debug(PS_COMP_PARAMETERS.parseString("('ls /')"))
log.debug(PS_COMP_EXPRESSION.parseString("sh.stdin(split=False)"))
log.debug(PS_COMP_EXPRESSION.parseString("sh('ls /')"))

###########################
# COMPONENTS SYNTAX SUGAR #
###########################

PS_COMP_SUGAR_FLOW = values.PS_FLOW.copy().addParseAction(
    lambda ts: ComponentBlueprint(PackageConstruct("_flowref", None), ParametersConstruct(ts[0]))
)

PS_COMP_SUGAR_VAR = values.PS_VAR.copy().addParseAction(
    lambda ts: ComponentBlueprint(PackageConstruct("var", None), ParametersConstruct(ts[0].reference))
)

PS_COMP_SUGAR_SHELL = QuotedString(quoteChar='`').setParseAction(
    lambda ts: ComponentBlueprint(PackageConstruct("sh", None), ParametersConstruct(ts[0]))
)


PS_COMP_SUGAR_ACCESSOR_ELEMENT = Word(srange("[a-zA-Z0-9_]"))
PS_COMP_SUGAR_ACCESSOR = (
    Suppress(symbols.GETSTART) +
    PS_COMP_SUGAR_ACCESSOR_ELEMENT + 
    ZeroOrMore(
        Suppress(symbols.IDSEP) + 
        PS_COMP_SUGAR_ACCESSOR_ELEMENT
    )
).setParseAction(
    lambda ts: ComponentBlueprint(PackageConstruct("get", None), ParametersConstruct(".".join(ts)))
)

PS_COMP_SUGAR_STRING = values.PS_STRING.copy().addParseAction(
    lambda ts: ComponentBlueprint(PackageConstruct("str", None), ParametersConstruct(ts[0]))
)

PS_COMP_SUGAR_INT = values.PS_INT.copy().addParseAction(
    lambda ts: ComponentBlueprint(PackageConstruct("int", None), ParametersConstruct(ts[0]))
)

PS_COMP_SUGAR_REAL = values.PS_REAL.copy().addParseAction(
    lambda ts: ComponentBlueprint(PackageConstruct("real", None), ParametersConstruct(ts[0]))
)


PS_SUGAR_COMP = Or([
    PS_COMP_SUGAR_FLOW,
    PS_COMP_SUGAR_VAR,
    PS_COMP_SUGAR_SHELL,
    PS_COMP_SUGAR_ACCESSOR,
    PS_COMP_SUGAR_STRING,
    PS_COMP_SUGAR_REAL,
    PS_COMP_SUGAR_INT
])

PS_COMP = Or([
    PS_COMP_EXPRESSION,
    PS_SUGAR_COMP
])

PS_COMP_CHAIN = And([
    PS_COMP,
    ZeroOrMore(
        Or(['|', '>']) + 
        PS_COMP
    )
]).addParseAction(
    lambda ts: [ts]   
)


log.debug("-------------------------------")
log.debug(PS_COMP.parseString("@flow"))
log.debug(PS_COMP.parseString("$var.foo.bar.baz"))
log.debug(PS_COMP.parseString("~a.0.b"))
log.debug(PS_COMP.parseString("`ls /`"))

log.debug(PS_COMP.parseString("`ls /`")[0].build(keywords.SOURCE))
log.debug(PS_COMP.parseString("-1.2")[0].build(keywords.SOURCE))


log.debug(OneOrMore(PS_COMP).parseString("@flow @out @in"))

