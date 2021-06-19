#!/usr/bin/python3
import pyparsing as pp
from pyparsing import srange, nums, quotedString, Literal, Word, Keyword, Combine, QuotedString, Optional, Suppress, ZeroOrMore, OneOrMore, MatchFirst, Each, Or, And, StringEnd
from actuator.package import REGISTRY
from actuator.flows import flowset, flow
from actuator import log, util
from actuator.lang import keywords, symbols, values, components, flows

from actuator.lang.construct import FlowReference, VariableReference, PackageConstruct, ParametersConstruct, ComponentBlueprint


###########################
# FLOW EXPRESSION PARSING #
###########################

PS_SEG = (
    Or([
        MatchFirst([
            keywords.SOURCE,
            keywords.OPERATOR,
            keywords.SINK,
            keywords.MONITOR
        ]) + components.PS_COMP
        ,
        keywords.FLOW + values.PS_IDENTIFIER
    ])
).setParseAction(
    lambda ts: [[ts[0], ts[1] if ts[0] == keywords.FLOW else ts[1].build(ts[0])]]
)

PS_SEG_SOURCE = (Keyword(keywords.SOURCE) + components.PS_COMP).setParseAction(
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
            sink = cb.build(keywords.SINK)
            newop = SinkOperator(sink)
        else:
            raise Exception("Faield to construct operator pipeline") 
        if op: newop.set_upstream(op)
        op = newop
        
    return [[kw, op]]
                
PS_SEG_OPERATOR = (Keyword(keywords.OPERATOR) + components.PS_COMP_CHAIN).setParseAction(build_seg_operator)


PS_SEG_SINK = (Keyword(keywords.SINK) + components.PS_COMP).setParseAction(
    lambda ts: [[ts[0], ts[1].build(ts[0])]]
)


PS_SEG_MONITOR = (Keyword(keywords.MONITOR) + components.PS_COMP).setParseAction(
    lambda ts: [[ts[0], ts[1].build(ts[0])]]
)

PS_SEG_NAME = (Keyword(keywords.FLOW) + values.PS_IDENTIFIER).setParseAction(
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


def build_flow(ts):
    kv = dict(list(ts))
    operator = kv.get(keywords.OPERATOR, None)
    sink = kv.get(keywords.SINK, None)
    source = kv.get(keywords.SOURCE, None)
    name = kv.get(keywords.FLOW, None)
    monitor = kv.get(keywords.MONITOR, None)
    return flow.Flow(source, sink, operator, monitor, name)
    
PS_FLOW_EXPRESSION = OneOrMore(PS_SEG).setParseAction(build_flow)

log.debug("-------------------------------")
log.debug(PS_FLOW_EXPRESSION.parseString("flow a from `ls /` via fmt.fromjson to $var on start"))

PS_FLOWSET_EXPRESSION = (
    PS_FLOW_EXPRESSION +
    ZeroOrMore(
        Suppress(symbols.FLOWSEP) + PS_FLOW_EXPRESSION
    ) +
    Optional(Suppress(symbols.FLOWSEP)) + 
    StringEnd()
)
log.debug("-------------------------------")
log.debug(PS_FLOWSET_EXPRESSION.parseString("flow a from `ls /` via fmt.fromjson to @out on start; flow out;"))



def parse(expression):
    from actuator.flows import flowset as mod_flowset
    flows = PS_FLOWSET_EXPRESSION.parseString(expression)
    flowset = mod_flowset.FlowSet(flows)
    return flowset

