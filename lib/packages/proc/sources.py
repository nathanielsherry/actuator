import subprocess
import psutil
from actuator.components import source
from actuator import util


from actuator.components.decorators import parameter, argument, input, output, allparameters, source


def ps(keys=None):
    if not keys:
        keys = list(psutil.Process().as_dict().keys())
    processes = []
    for proc in psutil.process_iter(keys):
        processes.append(proc.as_dict(attrs=keys))
    return processes


@output('list[dict{str: str}]', 'Information about running processes')
@argument('keys', 'list[str]', ['pid', 'name', 'username', 'cmdline', 'cpu_percent', 'uids', 'gids', 'nice', 'status', 'cwd'], 'Properties to access, returns all properties by default.')
@source
def info(keys):
    return ps(keys)

@output('list[str]', 'Specific value for running processes')
@argument('key', 'str', None, 'The name of the property to access')
@source
def get(key):
    return [p[key] for p in ps([key] if key else None)]        


@output('list[str]', 'Names of running processes')
@source
def names(self):
    return [p['name'] for p in ps(['name'])]



def do_search(search, keys):
    search_keys = list(search.keys())
    
    def check(entry):
        for key in search_keys:
            if entry[key] != search[key]:
                return False
        return True
    
    processes = []
    all_keys = list(set(keys + search_keys))
    if len(all_keys) == 0: return []
    data = ps(all_keys)
    data = [d for d in data if check(d)]
    return data

@output('list[str]', 'Information for matching processes')
@argument('keys', 'list[str]', ['pid', 'name', 'username', 'cmdline', 'cpu_percent', 'uids', 'gids', 'nice', 'status', 'cwd'], 'Properties to access, returns all properties by default.')
@allparameters('search')
@source
def search(keys, search):
    return do_search(search, keys)
                 

@output('bool', 'True if there are matching processes, False otherwise')
@allparameters('search')
@source
def has(search):
    data = do_search(search, [])
    return len(data) > 0
                        
