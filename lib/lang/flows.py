from actuator.lang import symbols, keywords, values, components

from pyparsing import Or, MatchFirst, Keyword, ZeroOrMore, OneOrMore, Suppress, Optional, StringEnd

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
