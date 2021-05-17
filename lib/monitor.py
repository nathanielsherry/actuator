#!/usr/bin/python3

import time
from actuator import log, util


def parse(tester, action, arg):
    name, config = arg.split(":", maxsplit=1)
    
    mon = None
    if name == "poll":
        config = util.read_args_kv(config)
        mon = PollMonitor(tester, action, config)
        
    return mon
        

class Monitor(util.BaseClass):
    def start(self):
        raise Exception("Unimplemented")
        

#Monitors the result of a Tester over time, triggering an event (callback) 
#when the value changes, passing the new state as the single argument.
class PollMonitor(Monitor):
    def __init__(self, tester, action, config):
        self._tester = tester
        self._action = action
        self._always_change = util.parse_bool(config['always'])
        
    def start(self):
        log.info("Starting {name} with test {test} and action {action}".format(name=self.name, test=self._tester, action=self._action))
        last_state = None
        new_state = False
        while True:
            new_state = self._tester.value
            if new_state != last_state or self._always_change == True:
                log.info("{name} yields {state}, running action.".format(name=self.name, state=new_state))
                self._action.perform(state=new_state)
                last_state = new_state
            time.sleep(min(10, self._tester.delay))

    


