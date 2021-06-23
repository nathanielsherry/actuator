import subprocess
from actuator.components import source
from actuator import util

class ShellSource(source.Source):
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
        
        
class StdinSource(source.Source):
    def initialise(self, *args, **kwargs):
        super().initialise(*args, **kwargs)
        self._split = util.parse_bool(kwargs.get('split', 'true'))

        
    @property
    def value(self):
        import sys

        if sys.stdin.closed: 
            return None
        
        if not self._split:
            lines = []
            for line in sys.stdin:
                if not line: break 
                lines.append(line.strip())
            return "\n".join(lines)
        else:
            line = sys.stdin.readline()
            if not line: return None
            return line.strip()
            

class JsonSource(source.Source):       
    @property
    def value(self):
        import sys, json

        if sys.stdin.closed:
            return None
        else:
            line = sys.stdin.readline()
            if not line: return None
            return json.loads(line.strip())
            

