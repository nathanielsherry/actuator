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
        self._tester = None
        self._action = None
    def start(self, tester, action):
        raise Exception("Unimplemented")
        

#Monitors the result of a Tester over time, triggering an event (callback) 
#when the value changes, passing the new state as the single argument.
class ChangeMonitor(Monitor):
    def __init__(self, config):
        super().__init__(config)
        
    def start(self, tester, action):
        log.info("Starting {name} with test {test} and action {action}".format(name=self.name, test=tester, action=action))
        last_state = None
        new_state = None
        while True:
            new_state = tester.value
            if new_state != last_state:
                log.info("{name} yields '{state}' ({result}), running action.".format(name=self.name, result="changed" if new_state != last_state else "unchanged", state=util.short_string(new_state)))
                action.perform(state=new_state)
                last_state = new_state
            time.sleep(tester.delay)

    

class LoopMonitor(Monitor):
    def __init__(self, config):
        super().__init__(config)
        
    def start(self, tester, action):
        while True:
            action.perform(state=tester.value)
            time.sleep(tester.delay)
            

class TrueStateMonitor(Monitor):
    def __init__(self, config):
        super().__init__(config)
        
    def start(self, tester, action):
        while True:
            state=tester.value
            if state == True: action.perform()
            time.sleep(tester.delay)

class StartMonitor(Monitor):
    def __init__(self, config):
        super().__init__(config)
        
    def start(self, tester, action):
        action.perform(state=tester.value)
