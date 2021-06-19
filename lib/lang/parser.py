#!/usr/bin/python3

def parse_flowset(expression):
    from actuator.flows import flowset as mod_flowset
    from actuator.lang import flows as flowsparser
    flows = flowsparser.PS_FLOWSET_EXPRESSION.parseString(expression)
    flowset = mod_flowset.FlowSet(flows)
    return flowset

