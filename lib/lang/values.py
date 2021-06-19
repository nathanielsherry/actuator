from actuator import util, log
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

