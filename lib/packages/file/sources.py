from actuator.components.source import Source

class FileSource(Source):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._filename = args[0]
        self._binary = util.parse_bool(kwargs.get('binary', 'false'))

    @property
    def value(self):
        read_string = 'r'
        if self._binary: read_string = 'rb'
        fh = open(self._filename, read_string)
        contents = fh.read()
        fh.close()
        return contents

