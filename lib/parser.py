from actuator import util

INSTRUCTION_SEPARATOR = '::'
PARAM_SEPARATOR = ','

KW_ACTION = "do"
KW_MONITOR = "on"
KW_STATE = "for"

def twosplit(s, delim):
    parts = s.split(delim, maxsplit=1)
    first = parts[0]
    second = ""
    if len(parts) > 1:
        second = parts[1]
    return first, second


from actuator.flexer import FlexParser, SequenceParserMixin, PrimitivesParserMixin

#A Sequence PARSER for reading values or sequences of values
class ActuatorExpressionMixin:
    def __init__(self):
        self._add_token_hook("act.state", lambda t: t == KW_STATE, lambda: self.parse_state())
        self._add_token_hook("act.action", lambda t: t == KW_ACTION, lambda: self.parse_action())
        self._add_token_hook("act.monitor", lambda t: t == KW_MONITOR, lambda: self.parse_monitor())
        
        from actuator import state
        self.add_instruction_hooks(state.instructions().keys())
        
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
        from actuator.flexer import Symbol
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
                for key in kwargs.keys():
                    value = kwargs[key]
                    if isinstance(value, Symbol):
                        kwargs[key] = value.name
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
    def parse_state(self):
        from actuator import state
        return self.parse_instruction(KW_STATE, lambda t: t in state.instructions().keys(), state.build)
    
    def parse_action(self):
        from actuator import action
        return self.parse_instruction(KW_ACTION, lambda t: t in action.instructions().keys(), action.build)
    
    def parse_monitor(self):
        from actuator import monitor
        return self.parse_instruction(KW_MONITOR, lambda t: t in monitor.instructions().keys(), monitor.build)
        
            
        
        
        
        
        

class ActuatorParser(FlexParser, SequenceParserMixin, PrimitivesParserMixin, ActuatorExpressionMixin):
    def __init__(self, exp):
        super().__init__(exp)
        


def parse_actuator_expression_shell(args):
    return parse_actuator_expression(" ".join(args))

def parse_actuator_expression(exp): 
    from actuator import state as mod_state
    from actuator import action as mod_action
    from actuator import monitor as mod_monitor

    f = ActuatorParser(exp)
    parts = f.parse()
    result = {'expression': exp}
    for part in parts:
        if isinstance(part, mod_state.State):
            if 'state' in result:
                raise Exception("Found more than one state")
            result['state'] = part
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
    
    if not 'monitor' in result:
        result['monitor'] = mod_monitor.LoopMonitor({'delay': '2'})
    if not 'action' in result:
        result['action'] = mod_action.PrintState({})
    
    return result
    

