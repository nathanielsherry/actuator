#!/usr/bin/python3

import time
from actuator import log, util, parser


def instructions():
    return {
        "change": ChangeMonitor,
        "loop": LoopMonitor,
        "start": StartMonitor,
        "true": TrueStateMonitor,
    }
    

def build(instruction, kwargs):
    return instructions()[instruction](kwargs)



class Monitor(util.BaseClass):
    def __init__(self, config):
        self._state = None
        self._action = None
    def start(self, state, action):
        raise Exception("Unimplemented")
        

#Monitors the result of a State over time, triggering an event (callback) 
#when the value changes, passing the new state as the single argument.
class ChangeMonitor(Monitor):
    def __init__(self, config):
        super().__init__(config)
        self._delay = config.get('delay', None)
        if self._delay: 
            self._delay = int(self._delay)
    
    @property
    def delay(self):
        return self._delay
    
    def start(self, state, action):
        log.info("Starting {name} with test {test} and action {action}".format(name=self.name, test=state, action=action))
        last_state = None
        new_state = None
        while True:
            new_state = state.value
            if new_state != last_state:
                log.info("{name} yields '{state}' ({result}), running action.".format(name=self.name, result="changed" if new_state != last_state else "unchanged", state=util.short_string(new_state)))
                action.perform(state=new_state)
                last_state = new_state
            time.sleep(self.delay or state.delay)

    

class LoopMonitor(Monitor):
    def __init__(self, config):
        super().__init__(config)
        
    def start(self, state, action):
        while True:
            action.perform(state=state.value)
            time.sleep(state.delay)
            

class TrueStateMonitor(Monitor):
    def __init__(self, config):
        super().__init__(config)
        
    def start(self, state, action):
        while True:
            if state.value == True: action.perform()
            time.sleep(state.delay)

class StartMonitor(Monitor):
    def __init__(self, config):
        super().__init__(config)
        
    def start(self, state, action):
        action.perform(state=state.value)
