from actuator import util

INSTRUCTION_SEPARATOR = '::'
PARAM_SEPARATOR = ','

def twosplit(s, delim):
    parts = s.split(delim, maxsplit=1)
    first = parts[0]
    second = ""
    if len(parts) > 1:
        second = parts[1]
    return first, second

#Reads an arg as comma separated k=v pairs 
def parse_args_kv(arg):
    if arg == None: return {}
    params = parse_args_list(arg)
    parameters = {}
    for param in params:
        key, value = twosplit(param, "=")
        parameters[key] = value
    return parameters

#Reads an arg as comma separated list 
def parse_args_list(arg):
    if arg == None: return []
    return arg.split(",")

def parse_actuator_expression_shell(args):
    return parse_actuator_expression(" ".join(args))
    
def parse_actuator_expression(exp):
    from actuator import action as mod_action
    from actuator import tester as mod_tester
    from actuator import monitor as mod_monitor
    
    parts = exp.split(" ")
    
    mon = None
    test = None
    action = None
    
    while len(parts) >= 2:
        kw = parts[0]
        info = parts[1]
        parts = parts[2:]
        
        if kw == "on": mon = info
        if kw == "do": action = info
        if kw == "with": test = info

        if len(parts) == 1:
            raise Exception("unknown argument {}".format(parts[0]))

    
    test = mod_tester.parse(test)
    action = mod_action.parse(action)
    mon = mod_monitor.parse(test, action, mon)
    
    return mon
    

def build_from_info(arg, lookup):
    chain = arg.split(INSTRUCTION_SEPARATOR)
    
    inner = None
    if len(chain) > 1:
        inner = build_from_info(INSTRUCTION_SEPARATOR.join(chain[:-1]), lookup)
        arg = chain[-1]
    
    instruction, config = twosplit(arg, PARAM_SEPARATOR)
    mode = lookup[instruction][1]
    if mode == 'args':
        config = {'args': parse_args_list(config)}
    elif mode == 'kwargs':
        config = parse_args_kv(config)
    if inner: config['inner'] = inner
    
    return lookup[instruction][0](config)


