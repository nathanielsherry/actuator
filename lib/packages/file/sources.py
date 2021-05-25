from actuator.source import Source

class FileSource(Source):
    def __init__(self, config):
        super().__init__(config)
        self._filename = config['args'][0]
        self._binary = util.parse_bool(config.get('binary', 'false'))

    @property
    def value(self):
        read_string = 'r'
        if self._binary: read_string = 'rb'
        fh = open(self._filename, read_string)
        contents = fh.read()
        fh.close()
        return contents

