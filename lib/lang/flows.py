from actuator.lang import symbols, keywords, values, components

from pyparsing import Or, MatchFirst, Keyword, ZeroOrMore, OneOrMore, Suppress, Optional, StringEnd

###########################
# FLOW EXPRESSION PARSING #
###########################


PS_SEG_SOURCE_VALUE = components.PS_COMP.copy().setParseAction(
    lambda ts: ts[0].build(keywords.SOURCE)
)
PS_SEG_SOURCE = (Suppress(Keyword(keywords.SOURCE)) + PS_SEG_SOURCE_VALUE).setParseAction(
    lambda ts: [[keywords.SOURCE, ts[0]]]
)

def build_seg_operator(kw, ts):
    opchain = ts[:]

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
        
    return op

PS_SEG_OPERATOR_VALUE = components.PS_COMP_CHAIN.copy().addParseAction(
    lambda ts: build_seg_operator(keywords.OPERATOR, ts)
)
PS_SEG_OPERATOR = (Suppress(Keyword(keywords.OPERATOR)) + PS_SEG_OPERATOR_VALUE).setParseAction(
    lambda ts: [[keywords.OPERATOR, ts[0]]]
)



PS_SEG_SINK_VALUE = components.PS_COMP.copy().setParseAction(
    lambda ts: ts[0].build(keywords.SINK)
)
PS_SEG_SINK = (Suppress(Keyword(keywords.SINK)) + PS_SEG_SINK_VALUE).setParseAction(
    lambda ts: [[keywords.SINK, ts[0]]]
)


PS_SEG_MONITOR_VALUE = components.PS_COMP.copy().setParseAction(
    lambda ts: ts[0].build(keywords.MONITOR)
)
PS_SEG_MONITOR = (Suppress(Keyword(keywords.MONITOR)) + PS_SEG_MONITOR_VALUE).setParseAction(
    lambda ts: [[keywords.MONITOR, ts[0]]]
)



PS_SEG_NAME_VALUE = values.PS_IDENTIFIER.copy().setParseAction(
    lambda ts: ts
)
PS_SEG_NAME = (Keyword(keywords.FLOW) + PS_SEG_NAME_VALUE).setParseAction(
    lambda ts: [ts]
)

PS_SEG = Or([
    PS_SEG_SOURCE,
    PS_SEG_OPERATOR,
    PS_SEG_SINK,
    PS_SEG_MONITOR,
    PS_SEG_NAME,
])


def build_flow(ts):
    from actuator.flows.flow import Flow
    kv = dict(list(ts))
    operator = kv.get(keywords.OPERATOR, None)
    sink = kv.get(keywords.SINK, None)
    source = kv.get(keywords.SOURCE, None)
    name = kv.get(keywords.FLOW, None)
    monitor = kv.get(keywords.MONITOR, None)
    return Flow(source, sink, operator, monitor, name)
    
PS_FLOW_EXPRESSION = OneOrMore(PS_SEG).setParseAction(build_flow)

PS_FLOWSET_EXPRESSION = (
    PS_FLOW_EXPRESSION +
    ZeroOrMore(
        Suppress(symbols.FLOWSEP) + PS_FLOW_EXPRESSION
    ) +
    Optional(Suppress(symbols.FLOWSEP)) + 
    StringEnd()
)


import unittest
class FlowTests(unittest.TestCase):
    
    def test_seg_from(self):
        kw, c = PS_SEG.parseString("from 'asdf'")[0]
        self.assertEqual(kw, keywords.SOURCE)

    def test_seg_via(self):
        from actuator.components.component import Component
        kw, c = PS_SEG.parseString("via fmt.tojson(pretty=True)")[0]
        self.assertEqual(kw, keywords.OPERATOR)
        self.assertTrue(isinstance(c, Component))

    def test_seg_to(self):
        kw, c = PS_SEG.parseString("to var('asdf')")[0]
        self.assertEqual(kw, keywords.SINK)
        
    def test_seg_on(self):
        kw, c = PS_SEG.parseString("on start")[0]
        self.assertEqual(kw, keywords.MONITOR)
