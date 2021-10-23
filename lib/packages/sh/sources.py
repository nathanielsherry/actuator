import subprocess
from actuator.components.source import Source 
from actuator import util

from actuator.components.decorators import parameter, argument, input, output, allarguments, source

class ShellSource(Source):
    def initialise(self, *args, **kwargs):
        super().initialise(*args, **kwargs)
        self._args = args
        self._shell = False
        if len(self._args) == 1 and ' ' in self._args[0]:
            self._shell = True
        
    @property
    def value(self):
        proc = subprocess.run(self._args, stdout=subprocess.PIPE, shell=self._shell)
        return proc.stdout.decode()
        
@parameter('split', 'bool', True, 'Split inputs by line')
@source
def stdin(split=True):
    import sys

    if sys.stdin.closed: 
        return None
    
    if not split:
        lines = []
        for line in sys.stdin:
            if not line: break 
            lines.append(line.strip())
        return "\n".join(lines)
    else:
        line = sys.stdin.readline()
        if not line: return None
        return line.strip()

