#!/usr/bin/python3

from actuator import log, util

def parse(action_string):
    parts = action_string.split(':', maxsplit=1)
    name = parts[0]
    config = None
    if len(parts) >= 2:
        config = parts[1]
    
    action = None
    if name == "systemd":
        config = util.read_args_kv(config)
        action = SystemdToggle(config)
    elif name == "shell":
        config = util.read_args_list(config)
        action = ShellRunner(config)
    elif name == "echo":
        config = util.read_args_kv(config)
        action = EchoToggle(config)
    elif name == "printmsg":
        config = util.read_args_kv(config)
        action = PrintMessageRunner(config)
    elif name == "printstate":
        config = util.read_args_kv(config)
        action = PrintStateToggle(config)
    
    return action
    


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
        
        
class EchoToggle(Toggle):
    def __init__(self, config):
        self._true_msg = config['true']
        self._false_msg = config['false']
        
    def toggle(self, state):
        log.info(self._true_msg if state else self._false_msg)
        

class PrintMessageRunner(Runner):
    def __init__(self, config):
        self._msg = config.get('msg', 'message')
    def run(self):
        print(self._msg, flush=True)
        
class PrintStateToggle(Toggle):
    def __init__(self, config):
        pass
    def toggle(self, state):
        log.info(state)
