from actuator.components.source import Source
from actuator import log, util

from actuator.components.decorators import parameter, argument, input, output, allarguments, source


def show_session(session):
    import subprocess
    result = subprocess.run(['loginctl', 'show-session', str(session)], capture_output=True)
    if not result.returncode == 0:
        raise Exception("Cannot get status of service {}:\n{}".format(session, result.stderr.decode()))
    data = {}
    for line in result.stdout.decode().split("\n"):
        line = line.strip()
        if not line: continue
        key, value = line.split("=", maxsplit=1)
        data[key] = value
    return data

@output('dict', "Dictionary of values returned by 'loginctl show-session <ID>'")
@argument('session', 'int', 1, 'Session ID to query', parser=int)
@source
def info(session):
    return show_session(session)



@output('bool', "Tests if session <ID> is locked")
@argument('session', 'int', 1, 'Session ID to query', parser=int)
@source
def locked(session):
    value = show_session(session)
    return value['LockedHint'] == 'yes'

