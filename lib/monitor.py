#!/usr/bin/python3

import time
from actuator import log, util, parser


def parse(tester, action, arg):
    instruction, config = parser.twosplit(arg, parser.PARAM_SEPARATOR)
    config = parser.parse_args_kv(config)
    
    mon = None
    if instruction == "change":
        mon = ChangeMonitor(tester, action, config)
    if instruction == "always":
        mon = ChangeMonitor(tester, action, config)
        
    return mon
        

class Monitor(util.BaseClass):
    def __init__(self, tester, action, config):
        self._tester = tester
        self._action = action
    def start(self):
        raise Exception("Unimplemented")
        

#Monitors the result of a Tester over time, triggering an event (callback) 
#when the value changes, passing the new state as the single argument.
class ChangeMonitor(Monitor):
    def __init__(self, tester, action, config):
        super().__init__(tester, action, config)
        self._always_change = util.parse_bool(config.get('always', 'false'))
        
    def start(self):
        log.info("Starting {name} with test {test} and action {action}".format(name=self.name, test=self._tester, action=self._action))
        last_state = None
        new_state = None
        while True:
            new_state = self._tester.value
            if new_state != last_state or self._always_change == True:
                log.info("{name} yields '{state}' ({result}), running action.".format(name=self.name, result="changed" if new_state != last_state else "unchanged", state=util.short_string(new_state)))
                self._action.perform(state=new_state)
                last_state = new_state
            time.sleep(min(10, self._tester.delay))

    

class AlwaysMonitor(Monitor):
    def __init__(self, tester, action, config):
        super().__init__(tester, action, config)
