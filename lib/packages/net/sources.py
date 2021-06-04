from actuator import util
from actuator.components import source

class URLSource(source.Source):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._url = args[0]
        self._text_only = util.parse_bool(kwargs.get('html-to-text', 'false'))
        
    @property
    def value(self):
        result = util.get_url(self._url)
        if self._text_only:
            from html2text import html2text
            result = html2text(result)
        return result
