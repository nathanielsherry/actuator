from actuator.components import sink

from actuator.components.decorators import parameter, argument, input, output, allarguments

@parameter('mode', 'str', 'a', 'Mode to open file with')
@argument('filename', 'str', None, 'Name of file to which the payload will be written')
class FileSink(sink.Sink):
    """
    Append (or write) a string conversion of the payload to a file.
    """        
    def perform(self, payload):
        fh = open(self.args.filename, self.params.mode)
        
        if 'b' in self.params.mode: 
            #Binary mode
            if not isinstance(payload, bytes): payload = str(payload).encode()
        else:
            #text mode
            payload = str(payload).encode()
        
        fh.write(payload)
        fh.close()
        
        
