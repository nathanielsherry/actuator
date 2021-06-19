#!/usr/bin/python3
import pyparsing as pp
from pyparsing import srange, nums, quotedString, Literal, Word, Keyword, Combine, QuotedString, Optional, Suppress, ZeroOrMore, OneOrMore, MatchFirst, Each, Or, And, StringEnd
from actuator.lang.parser import Reference, FlowReference, VariableReference, Construct
from actuator.lang import parser as act_parser
from actuator.package import REGISTRY
from actuator.flows import flowset
from actuator import log, util

SYM_FLOWSEP = ';'
SYM_IDSEP = "."
SYM_VARSTART = '$'
SYM_FLOWREF = '@'
SYM_GETSTART = '~'
KW_SINK = "to"
KW_MONITOR = "on"
KW_SOURCE = "from"
KW_OPERATOR = "via"
KW_FLOW = "flow"
KEYWORDS = [KW_SOURCE, KW_SINK, KW_MONITOR, KW_OPERATOR, KW_FLOW]


#A sketch of what a component should look like eventually, a highly cusomized factory
class ComponentBlueprint(Construct):
    def __init__(self, package, params):
        self._package = package
        self._params = params
      
    @property
    def name(self):
        return self.package.path
    
    @property
    def package(self):
        return self._package
    
    #Build the component. Here, 'role' represents the part of the flow
    #expression this component will be, source, sink, operator, monitor
    def build(self, role):
        builder = None
        if role == KW_SOURCE:
            builder = REGISTRY.lookup_source(self.package.path)
        elif role == KW_OPERATOR:
            builder = REGISTRY.lookup_operator(self.package.path)
        elif role == KW_SINK:
            builder = REGISTRY.lookup_sink(self.package.path)
        elif role == KW_MONITOR:
            builder = REGISTRY.lookup_monitor(self.package.path)
        
        if not builder:
            raise Exception("Could not build {name}".format(name=self.package.path))
        
        args = self._params.args
        kwargs = self._params.kwargs
        component = builder(*args, **kwargs)
        
        return component


class PackageConstruct(Construct):
    def __init__(self, package, element):
        self._package = package
        self._element = element
    
    @property
    def name(self): return self.path
    
    @property
    def package(self): return self._package
    
    @property
    def element(self): return self._element
    
    @property
    def path(self): return self.package + ("." + self.element if self.element else "")

class ParametersConstruct(Construct):
    def __init__(self, *args, **kwargs):
        self._args = list(args)
        self._kwargs = dict(kwargs)
    
    @property
    def name(self): return "{}, {}".format(self.args, self.kwargs)
    
    @property
    def args(self): return self._args
    
    @property
    def kwargs(self): return self._kwargs

    


PS_IDENTIFIER = Word(srange("[a-zA-Z_]"), srange("[a-zA-Z0-9_]"))

PS_DOT_IDENTIFIER = (
    PS_IDENTIFIER + 
    ZeroOrMore(
        Suppress(SYM_IDSEP) + 
        PS_IDENTIFIER
    )
).leaveWhitespace()


PS_FLOW = (
    Suppress(SYM_FLOWREF) + PS_IDENTIFIER
).setParseAction(
    lambda ts: FlowReference(".".join(ts))
)

PS_VAR = (
    Suppress(SYM_VARSTART) + PS_DOT_IDENTIFIER
).setParseAction(
    lambda ts: VariableReference(".".join(ts))
)

PS_INT = Combine(
    Optional("-") + 
    Word(nums)
).setParseAction(
    lambda ts: int(ts[0])
)

PS_REAL = Combine(
    Optional("-") + 
    Word(nums) + 
    '.' + 
    Word(nums)
).setParseAction(
    lambda ts: float(ts[0])
)

PS_STRING = Or([
    QuotedString(quoteChar='"'),
    QuotedString(quoteChar="'"),
])

PS_BOOL = Or(["True", "False"]).setParseAction(
    lambda ts: util.parse_bool(ts[0])
)


PS_VALUE = Or([
    PS_FLOW,
    PS_VAR,
    PS_INT,
    PS_REAL,
    PS_STRING,
    PS_BOOL,
])


log.debug(PS_VALUE.parseString("'asdf'"))
log.debug(PS_VALUE.parseString("1"))
log.debug(PS_VALUE.parseString("1.1"))
log.debug(PS_VALUE.parseString("-1"))
log.debug(PS_VALUE.parseString("-1.1"))
log.debug(PS_VALUE.parseString("False"))
log.debug(PS_VALUE.parseString("@flow"))
log.debug(PS_VALUE.parseString("$var.bar"))

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
        PS_IDENTIFIER,
        PS_IDENTIFIER + Suppress(".") + PS_IDENTIFIER
]).setParseAction(build_comp_pkg)

PS_COMP_PARAMETER_KEY = PS_IDENTIFIER.copy()
PS_COMP_PARAMETER_VALUE = PS_VALUE.copy()
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

PS_COMP_SUGAR_FLOW = PS_FLOW.copy().addParseAction(
    lambda ts: ComponentBlueprint(PackageConstruct("_flowref", None), ParametersConstruct(ts[0]))
)

PS_COMP_SUGAR_VAR = PS_VAR.copy().addParseAction(
    lambda ts: ComponentBlueprint(PackageConstruct("var", None), ParametersConstruct(ts[0].reference))
)

PS_COMP_SUGAR_SHELL = QuotedString(quoteChar='`').setParseAction(
    lambda ts: ComponentBlueprint(PackageConstruct("sh", None), ParametersConstruct(ts[0]))
)


PS_COMP_SUGAR_ACCESSOR_ELEMENT = Word(srange("[a-zA-Z0-9_]"))
PS_COMP_SUGAR_ACCESSOR = (
    Suppress(SYM_GETSTART) +
    PS_COMP_SUGAR_ACCESSOR_ELEMENT + 
    ZeroOrMore(
        Suppress(SYM_IDSEP) + 
        PS_COMP_SUGAR_ACCESSOR_ELEMENT
    )
).setParseAction(
    lambda ts: ComponentBlueprint(PackageConstruct("get", None), ParametersConstruct(".".join(ts)))
)

PS_COMP_SUGAR_STRING = PS_STRING.copy().addParseAction(
    lambda ts: ComponentBlueprint(PackageConstruct("str", None), ParametersConstruct(ts[0]))
)

PS_COMP_SUGAR_INT = PS_INT.copy().addParseAction(
    lambda ts: ComponentBlueprint(PackageConstruct("int", None), ParametersConstruct(ts[0]))
)

PS_COMP_SUGAR_REAL = PS_REAL.copy().addParseAction(
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

log.debug(PS_COMP.parseString("`ls /`")[0].build(KW_SOURCE))
log.debug(PS_COMP.parseString("-1.2")[0].build(KW_SOURCE))


log.debug(OneOrMore(PS_COMP).parseString("@flow @out @in"))


###########################
# FLOW EXPRESSION PARSING #
###########################

PS_SEG = (
    Or([
        MatchFirst([
            KW_SOURCE,
            KW_OPERATOR,
            KW_SINK,
            KW_MONITOR
        ]) + PS_COMP
        ,
        KW_FLOW + PS_IDENTIFIER
    ])
).setParseAction(
    lambda ts: [[ts[0], ts[1] if ts[0] == KW_FLOW else ts[1].build(ts[0])]]
)

PS_SEG_SOURCE = (Keyword(KW_SOURCE) + PS_COMP).setParseAction(
    lambda ts: [[ts[0], ts[1].build(ts[0])]]
)

def build_seg_operator(ts):
    kw = ts[0]
    opchain = ts[1][:]
    
    op = opchain.pop(0).build(kw)
    code = None
    
    while opchain:
        code = opchain.pop(0)
        cb = opchain.pop(0)
        if code == "|" or code == None:
            newop = cb.build(kw)
        elif code == ">" and op != None:
            sink = cb.build(KW_SINK)
            newop = SinkOperator(sink)
        else:
            raise Exception("Faield to construct operator pipeline") 
        if op: newop.set_upstream(op)
        op = newop
        
    return [[kw, op]]
                
PS_SEG_OPERATOR = (Keyword(KW_OPERATOR) + PS_COMP_CHAIN).setParseAction(build_seg_operator)


PS_SEG_SINK = (Keyword(KW_SINK) + PS_COMP).setParseAction(
    lambda ts: [[ts[0], ts[1].build(ts[0])]]
)


PS_SEG_MONITOR = (Keyword(KW_MONITOR) + PS_COMP).setParseAction(
    lambda ts: [[ts[0], ts[1].build(ts[0])]]
)

PS_SEG_NAME = (Keyword(KW_FLOW) + PS_IDENTIFIER).setParseAction(
    lambda ts: [ts]
)

PS_SEG = Or([
    PS_SEG_SOURCE,
    PS_SEG_OPERATOR,
    PS_SEG_SINK,
    PS_SEG_MONITOR,
    PS_SEG_NAME,
])


log.debug("-------------------------------")
log.debug(PS_SEG.parseString("from `ls /`"))
log.debug(PS_SEG.parseString("via fmt.tojson(pretty=True)"))
log.debug(PS_SEG.parseString("to var('asdf')"))



PS_FLOW_EXPRESSION = OneOrMore(PS_SEG).setParseAction(
    lambda ts: act_parser.makeflow(dict(list(ts)))
)

log.debug("-------------------------------")
log.debug(PS_FLOW_EXPRESSION.parseString("flow a from `ls /` via fmt.fromjson to $var on start"))

PS_FLOWSET_EXPRESSION = (
    PS_FLOW_EXPRESSION +
    ZeroOrMore(
        Suppress(SYM_FLOWSEP) + PS_FLOW_EXPRESSION
    ) +
    Optional(Suppress(SYM_FLOWSEP)) + 
    StringEnd()
)
log.debug("-------------------------------")
log.debug(PS_FLOWSET_EXPRESSION.parseString("flow a from `ls /` via fmt.fromjson to @out on start; flow out;"))



def parse(expression):
    from actuator.flows import flowset as mod_flowset
    flows = PS_FLOWSET_EXPRESSION.parseString(expression)
    flowset = mod_flowset.FlowSet(flows)
    return flowset

