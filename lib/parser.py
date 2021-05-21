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
    
def parse_actuator_expression_old(exp):
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

    
    if mon == None: mon = "all"
    test = mod_tester.parse(test)
    action = mod_action.parse(action)
    mon = mod_monitor.parse(test, action, mon)
    
    return mon


from actuator.flexer import FlexParser, SequenceParserMixin, PrimitivesParserMixin

#A Sequence PARSER for reading values or sequences of values
class ActuatorExpressionMixin:
    def __init__(self):
        self._add_token_hook("act.tester", lambda t: t == "with", lambda: self.parse_tester())
        self._add_token_hook("act.action", lambda t: t == "do", lambda: self.parse_action())
        self._add_token_hook("act.monitor", lambda t: t == "on", lambda: self.parse_monitor())
        
        from actuator import tester
        self.add_instruction_hooks(tester.instructions().keys())
        
        from actuator import action
        self.add_instruction_hooks(action.instructions().keys())
        
        from actuator import monitor
        self.add_instruction_hooks(monitor.instructions().keys())
        
    def add_instruction_hooks(self, instructions):
        for instruction in instructions:
            self.add_instruction_hook(instruction)
    
    #This needs to be a separate function from add_instruction_hooks to 
    #complete the closure in the test fn
    def add_instruction_hook(self, instruction):
            try:
                self._add_value_hook(
                    "act.inst.{}".format(instruction), 
                    lambda t: t == instruction,
                    lambda: self.flexer.pop(instruction)
                )
            except:
                pass
    
    def parse_instruction(self, key, valid_instruction, build, inner=None):
        if key: key = self.flexer.pop(key)
        instruction = self.parse_value()
        if not valid_instruction(instruction):
            raise Exception("Invalid: '{}'".format(instruction))
        args = None
        kwargs = None
        while True:
            if self.flexer.peek() == '[':
                args = self.parse_list()
                continue
            if self.flexer.peek() == '(':
                kwargs = self.parse_keyvalue()
                continue
            break
        
        if not kwargs: 
            kwargs = {}
            
        if args:
            kwargs['args'] = args
            
        if inner:
            kwargs['inner'] = inner
        
        finished = build(instruction, kwargs)
        
        if self.flexer.pop_if('|') == '|':
            return self.parse_instruction(None, valid_instruction, build, inner=finished)
        else:
            return finished
        #return finished
        

    #Parses a list of items.
    def parse_tester(self):
        from actuator import tester
        return self.parse_instruction('with', lambda t: t in tester.instructions().keys(), tester.build)
    
    def parse_action(self):
        from actuator import action
        return self.parse_instruction('do', lambda t: t in action.instructions().keys(), action.build)
    
    def parse_monitor(self):
        from actuator import monitor
        return self.parse_instruction('on', lambda t: t in monitor.instructions().keys(), monitor.build)
        
            
        
        
        
        
        

class ActuatorParser(FlexParser, SequenceParserMixin, PrimitivesParserMixin, ActuatorExpressionMixin):
    def __init__(self, exp):
        super().__init__(exp)
        




def parse_actuator_expression(exp): 
    from actuator import tester as mod_tester
    from actuator import action as mod_action
    from actuator import monitor as mod_monitor

    f = ActuatorParser(exp)
    parts = f.parse()
    result = {}
    for part in parts:
        if isinstance(part, mod_tester.Tester):
            if 'tester' in result:
                raise Exception("Found more than one tester")
            result['tester'] = part
        elif isinstance(part, mod_action.Action):
            if 'action' in result:
                raise Exception("Found more than one action")
            result['action'] = part
        elif isinstance(part, mod_monitor.Monitor):
            if 'monitor' in result:
                raise Exception("Found more than one monitor")
            result['monitor'] = part
        else:
            raise Exception("Found unrecognised component")
    
    return result
    

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


