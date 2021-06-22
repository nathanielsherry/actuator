#!/usr/bin/python3

def parse_flowset(expression):
    from actuator.flows import flowset as mod_flowset
    from actuator.lang import flows as flowsparser
    flows = flowsparser.PS_FLOWSET_EXPRESSION.parseString(expression)
    flowset = mod_flowset.FlowSet(flows)
    return flowset

def parse_sink(expression):
    from actuator.lang import flows as flowsparser
    return flowsparser.SEG_SINK_VALUE.parseString(expression)[0]
    
def parse_source(expression):
    from actuator.lang import flows as flowsparser
    return flowsparser.PS_SEG_SOURCE_VALUE.parseString(expression)[0]

def parse_operator(expression):
    from actuator.lang import flows as flowsparser
    return flowsparser.PS_SEG_OPERATOR_VALUE.parseString(expression)[0]

def parse_monitor(expression):
    from actuator.lang import flows as flowsparser
    return flowsparser.PS_SEG_MONITOR_VALUE.parseString(expression)[0]

def parse_name(expression):
    from actuator.lang import flows as flowsparser
    return flowsparser.PS_SEG_NAME_VALUE.parseString(expression)[0]
