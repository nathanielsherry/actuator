from actuator.state import State
from actuator import util, state

class URLSource(State):
    def __init__(self, config):
        super().__init__(config)
        self._url = config['args'][0]
        self._text_only = util.parse_bool(config.get('html-to-text', 'false'))
        
    @property
    def delay(self): 
        return self._delay or state.DELAY_MEDIUM
    
    @property
    def value(self):
        result = util.get_url(self._url)
        if self._text_only:
            from html2text import html2text
            result = html2text(result)
        return result
