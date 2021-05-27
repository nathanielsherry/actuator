from actuator import sink


class FileSink(sink.Sink):
    def __init__(self, config):
        super().__init__(config)
        self._filename = config['args'][0]
        self._mode = config.get('mode', 'false')
        
    def perform(self, payload):
        fh = open(self._filename, self._mode)
        
        if 'b' in self._mode: 
            #Binary mode
            if not isinstance(payload, bytes): payload = str(payload).encode()
        else:
            #text mode
            payload = str(payload).encode()
        
        fh.write(payload)
        fh.close()
        
        
