#!/usr/bin/python3

from actuator import log, util, parser

def instructions():
    return {
        "systemd": SystemdToggle,
        "sh": ShellRunner,
        "printif": PrintIf,
        "printmsg": PrintRunner,
        "printstate": PrintToggle,
        "print": PrintAction,
    }
    
    
def build(instruction, kwargs):
    return instructions()[instruction](kwargs)    
    


class Action(util.BaseClass):
    def perform(self, **kwargs):
        raise Exception("Unimplemented")

class Toggle(Action):
    def perform(self, **kwargs):
        return self.toggle(kwargs['state'])
    def toggle(self, state):
        raise Exception("Unimplemented")

class Runner(Action):
    def perform(self, **kwargs):
        self.run()
    def run(self):
        raise Exception("Unimplemented")



#Runs an arbitrary shell command on activation
class ShellRunner(Runner):
    def __init__(self, config):
        self._exec = config[0]
        self._args = config[1:]

    def run(self):
        import subprocess
        subprocess.run([self._exec] + self._args)
        
        
class SystemdToggle(Toggle):
    def __init__(self, config):
        self._service = config['service']
        
    def toggle(self, state):
        import subprocess
        subprocess.run(["systemctl", "start" if state == True else "stop", self._service])
        
        
       
class PrintAction(Action):
    def __init__(self, config):
        pass
    def perform(self, **kwargs):
        import pprint
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(kwargs)

class PrintIf(Toggle):
    def __init__(self, config):
        self._true_msg = config['true']
        self._false_msg = config['false']
        
    def toggle(self, state):
        print(self._true_msg if state else self._false_msg)

class PrintToggle(Toggle):
    def __init__(self, config):
        pass
    def toggle(self, state):
        print(state)
        
class PrintRunner(Runner):
    def __init__(self, config):
        self._msg = config.get('msg', 'message')
    def run(self):
        print(self._msg, flush=True)
