import subprocess
from actuator import source

class ShellSource(source.Source):
    def __init__(self, config):
        super().__init__(config)
        self._args = config['args']
        self._shell = False
        if len(self._args) == 1 and ' ' in self._args[0]:
            self._shell = True
        
    @property
    def value(self):
        proc = subprocess.run(self._args, stdout=subprocess.PIPE, shell=self._shell)
        return proc.stdout.decode()
