from actuator.components.source import Source
from actuator import log, util

class Info(Source):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        log.debug("{name} received initial config {config}".format(name=self.name, config=(args, kwargs)))
        self._service = config['args'][0]

    @property
    def value(self):
        import subprocess
        result = subprocess.run(['systemctl', 'show', self._service], capture_output=True)
        if not result.returncode == 0:
            raise Exception("Cannot get status of service {}:\n{}".format(self._service, result.stderr.decode()))
        data = {}
        for line in result.stdout.decode().split("\n"):
            line = line.strip()
            if not line: continue
            key, value = line.split("=", maxsplit=1)
            data[key] = value
        return data
        

class State(Info):

    @property
    def value(self):
        value = super().value
        return value['ActiveState']
        
        
class Active(State):

    @property
    def value(self):
        value = super().value
        return value == 'active'
        
