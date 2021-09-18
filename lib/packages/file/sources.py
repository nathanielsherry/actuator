from actuator.components.source import Source

from actuator.components.decorators import parameter, argument, input, output, allarguments


@parameter('binary', 'bool', False, 'Open the file in binary mode')
@argument('filename', 'str', None, 'Name of file from which the payload will be read')
class FileSource(Source):
    @property
    def value(self):
        read_string = 'r'
        if self.params.binary: read_string = 'rb'
        fh = open(self.args.filename, read_string)
        contents = fh.read()
        fh.close()
        return contents

