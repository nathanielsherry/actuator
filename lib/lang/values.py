from actuator import util
from actuator.lang import symbols
from actuator.lang.construct import FlowReference, VariableReference

from pyparsing import srange, nums, Word, ZeroOrMore, Suppress, Combine, Optional, QuotedString, Or

PS_IDENTIFIER = Word(srange("[a-zA-Z_]"), srange("[a-zA-Z0-9_]"))

PS_DOT_IDENTIFIER = (
    PS_IDENTIFIER + 
    ZeroOrMore(
        Suppress(symbols.IDSEP) + 
        PS_IDENTIFIER
    )
).leaveWhitespace()


PS_FLOW = (
    Suppress(symbols.FLOWREF) + PS_IDENTIFIER
).setParseAction(
    lambda ts: FlowReference(".".join(ts))
)

PS_VAR = (
    Suppress(symbols.VARSTART) + PS_DOT_IDENTIFIER
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

PS_PRIMITIVE = Or([
    PS_INT,
    PS_REAL,
    PS_STRING,
    PS_BOOL,
])

PS_VALUE = Or([
    PS_FLOW,
    PS_VAR,
    PS_PRIMITIVE
])


import unittest
class ValueTests(unittest.TestCase):
    
    def test_string(self):
        self.assertEqual(PS_VALUE.parseString("'asdf'")[0], 'asdf')
        
    def test_int(self):
        self.assertEqual(PS_VALUE.parseString("1")[0], 1)
        self.assertEqual(PS_VALUE.parseString("-1")[0], -1)

    def test_float(self):
        self.assertEqual(PS_VALUE.parseString("1.1")[0], 1.1)
        self.assertEqual(PS_VALUE.parseString("-1.1")[0], -1.1)

    def test_bool(self):
        self.assertEqual(PS_VALUE.parseString("True")[0], True)
        self.assertEqual(PS_VALUE.parseString("False")[0], False)

    def test_flow(self):
        self.assertEqual(PS_VALUE.parseString("@flow")[0].reference, "flow")

    def test_var(self):
        self.assertEqual(PS_VALUE.parseString("$var.bar")[0].reference, "var.bar")


