#!/usr/bin/python3

import time
from actuator import log, util, parser


def instructions():
    return {
        "change": ChangeMonitor,
        "all": AlwaysMonitor,
    }
    

def build(instruction, kwargs):
    return instructions()[instruction](kwargs)



class Monitor(util.BaseClass):
    def __init__(self, config):
        self._tester = None
        self._action = None
    def start(self, tester, action):
        raise Exception("Unimplemented")
        

#Monitors the result of a Tester over time, triggering an event (callback) 
#when the value changes, passing the new state as the single argument.
class ChangeMonitor(Monitor):
    def __init__(self, config):
        super().__init__(config)
        self._always_change = util.parse_bool(config.get('always', 'false'))
        
    def start(self, tester, action):
        log.info("Starting {name} with test {test} and action {action}".format(name=self.name, test=tester, action=action))
        last_state = None
        new_state = None
        while True:
            new_state = tester.value
            if new_state != last_state or self._always_change == True:
                log.info("{name} yields '{state}' ({result}), running action.".format(name=self.name, result="changed" if new_state != last_state else "unchanged", state=util.short_string(new_state)))
                action.perform(state=new_state)
                last_state = new_state
            time.sleep(min(10, tester.delay))

    

class AlwaysMonitor(Monitor):
    def __init__(self, config):
        super().__init__(config)
        
    def start(self, tester, action):
        action.perform(state=tester.value)
