from actuator import util, source

class URLSource(source.Source):
    def __init__(self, config):
        super().__init__(config)
        self._url = config['args'][0]
        self._text_only = util.parse_bool(config.get('html-to-text', 'false'))
        
    @property
    def value(self):
        result = util.get_url(self._url)
        if self._text_only:
            from html2text import html2text
            result = html2text(result)
        return result
