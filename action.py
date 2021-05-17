#!/usr/bin/python3

import log, util

def parse(action_string):
    name, config = action_string.split(':', maxsplit=1)
    
    action = None
    if name == "systemd":
        config = util.read_args_kv(config)
        action = SystemdToggle(config['service'])
    elif name == "shell":
        config = util.read_args_list(config)
        action = ShellRunner(config[0], config[1:])
    elif name == "echo":
        config = util.read_args_kv(config)
        action = EchoToggle(true_msg=config['true'], false_msg=config['false'])
    
    return action
    


class Action(util.BaseClass):
    def perform(self, **kwargs):
        raise Exception("Unimplemented")

class Toggle(Action):
    def perform(self, state):
        raise Exception("Unimplemented")

class Runner(Action):
    def perform(self):
        raise Exception("Unimplemented")



#Runs an arbitrary shell command on activation
class ShellRunner(Runner):
    def __init__(self, execpath, args):
        self._exec = execpath
        self._args = args

    def perform(self):
        import subprocess
        subprocess.run([execpath] + args)
        
        
class SystemdToggle(Toggle):
    def __init__(self, service):
        self._service = service
        
    def perform(self, state):
        subprocess.run(["systemctl", "start" if boolean else "stop", self._service])
        
        
class EchoToggle(Toggle):
    def __init__(self, true_msg, false_msg):
        self._true_msg = true_msg
        self._false_msg = false_msg
        
    def perform(self, state):
        log.info(self._true_msg if state else self._false_msg)
