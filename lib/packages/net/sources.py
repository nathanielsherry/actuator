from actuator import util
from actuator.components import source
from actuator.components.decorators import parameter, argument, input, output, allarguments


class URLSource(source.Source):
    def initialise(self, *args, **kwargs):
        super().initialise(*args, **kwargs)
        self._url = args[0]
        self._text_only = util.parse_bool(kwargs.get('html-to-text', 'false'))
        
    @property
    def value(self):
        result = util.get_url(self._url)
        if self._text_only:
            from html2text import html2text
            result = html2text(result)
        return result

@output('bool', 'True if-and-only-if pingable')
@argument('address', 'str', '8.8.8.8', 'Address to ping')
class Pingable(source.Source):
    """
    Tests if an address is pingable. Emits boolean True if it is, and False otherwise.
    """
    @property
    def value(self):
        import subprocess
        result = subprocess.run(['ping', '-c', '3', self.args.accessor])
        return result.recurncode == 0

