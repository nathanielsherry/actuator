from actuator.components.source import Source
from actuator import log, util

class Info(Source):
    def initialise(self, *args, **kwargs):
        super().initialise(*args, **kwargs)
        log.debug("{kind} received initial config {config}".format(kind=self.kind, config=(args, kwargs)))
        self._session = args[0]

    @property
    def value(self):
        import subprocess
        result = subprocess.run(['loginctl', 'show-session', str(self._session)], capture_output=True)
        if not result.returncode == 0:
            raise Exception("Cannot get status of service {}:\n{}".format(self._session, result.stderr.decode()))
        data = {}
        for line in result.stdout.decode().split("\n"):
            line = line.strip()
            if not line: continue
            key, value = line.split("=", maxsplit=1)
            data[key] = value
        return data

        
class Locked(Info):

    @property
    def value(self):
        value = super().value
        return value['LockedHint'] == 'yes'

