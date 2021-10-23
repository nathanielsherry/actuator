from actuator import util
from actuator.components.source import Source
from actuator.components.decorators import parameter, argument, input, output, allarguments, source

@argument('url', 'str', None, 'URL to fetch')
@parameter('text', 'bool', False, 'Try to convert the document from HTML to Text')
@source
def get(url, text=False):
    result = util.get_url(url)
    if text:
        from html2text import html2text
        result = html2text(result)
    return result

@output('bool', 'True if-and-only-if pingable')
@argument('address', 'str', '8.8.8.8', 'Address to ping')
@source
def pingable(address):
    import subprocess
    result = subprocess.run(['ping', '-c', '3', address], stdout=subprocess.PIPE)
    return result.returncode == 0

