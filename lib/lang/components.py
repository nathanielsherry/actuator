from actuator.lang.construct import PackageConstruct, ParametersConstruct, ComponentBlueprint
from actuator.lang import symbols, keywords, values, accessor

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

PS_COMP_SUGAR_ACCESSOR = accessor.PS_ACCESSOR.copy().setParseAction(
    lambda ts: ComponentBlueprint(PackageConstruct("get", None), ParametersConstruct(*list(ts)))
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


import unittest
class ComponentTests(unittest.TestCase):
    
    def test_pkg(self):
        pc = PS_COMP_PKG.parseString("sh.stdin")[0]
        self.assertEqual(pc.path, "sh.stdin")
        self.assertEqual(pc.package, "sh")

    def test_param_kwargs(self):
        pc = PS_COMP_PARAMETERS.parseString("(foo=False, bar=1)")[0]
        self.assertTrue('bar' in pc.kwargs)
        self.assertEqual(pc.kwargs['foo'], False)
        self.assertEqual(pc.kwargs['bar'], 1)
        self.assertEqual(pc.args, [])
        
    def test_param_args(self):
        pc = PS_COMP_PARAMETERS.parseString("(1, 2, 3)")[0]
        self.assertEqual(pc.args, [1, 2, 3])
        self.assertEqual(pc.kwargs, {})
    
    def test_sugar_flow(self):
        cb = PS_COMP.parseString("@flowname")[0]
        self.assertEqual(cb.package.path, "_flowref")
        self.assertEqual(cb.parameters.args[0].reference, "flowname")
        c = cb.build(keywords.SINK)

    def test_sugar_var(self):
        cb = PS_COMP.parseString("$var.foo.bar.baz")[0]
        self.assertEqual(cb.package.path, "var")
        self.assertEqual(cb.parameters.args[0], "var.foo.bar.baz")
        c = cb.build(keywords.SINK)
    
    def test_sugar_accessor(self):
        cb = PS_COMP.parseString("~a.0.b")[0]
        self.assertEqual(cb.package.path, "get")
        self.assertEqual(cb.parameters.args, ['a', 0, 'b'])
        c = cb.build(keywords.OPERATOR)
        
    def test_sugar_shell(self):
        cb = PS_COMP.parseString("`ls /`")[0]
        self.assertEqual(cb.package.path, "sh")
        self.assertEqual(cb.parameters.args[0], "ls /")
        c = cb.build(keywords.SOURCE)
        
    def test_sugar_string(self):
        cb = PS_COMP.parseString("'abcd'")[0]
        self.assertEqual(cb.package.path, "str")
        self.assertEqual(cb.parameters.args[0], "abcd")
        c = cb.build(keywords.SOURCE)
        
    def test_sugar_int(self):
        cb = PS_COMP.parseString("-1")[0]
        self.assertEqual(cb.package.path, "int")
        self.assertEqual(cb.parameters.args[0], -1)
        c = cb.build(keywords.SOURCE)
        
    def test_sugar_float(self):
        cb = PS_COMP.parseString("-1.1")[0]
        self.assertEqual(cb.package.path, "real")
        self.assertEqual(cb.parameters.args[0], -1.1)
        c = cb.build(keywords.SOURCE)
        
    def test_exp_long(self):
        cb = PS_COMP_EXPRESSION.parseString("sh.stdin(split=False)")[0]
        self.assertEqual(cb.package.element, "stdin")
        self.assertEqual(cb.parameters.kwargs['split'], False)
        
    def test_exp_short(self):
        cb = PS_COMP_EXPRESSION.parseString("sh('ls /')")[0]
        self.assertEqual(cb.package.element, None)
        self.assertEqual(cb.parameters.args[0], 'ls /')
        
