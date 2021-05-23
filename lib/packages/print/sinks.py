from actuator import sink


class Print(sink.Sink):
    def __init__(self, config):
        super().__init__(config)
    def perform(self, **kwargs):
        if len(kwargs) == 1 and 'state' in kwargs:
            kwargs = kwargs['state']
            
        if isinstance(kwargs, str):
            print(kwargs, flush=True)
        else:
            import pprint
            pp = pprint.PrettyPrinter(indent=4)
            pp.pprint(kwargs)

class PrintIf(sink.ToggleSink):
    def __init__(self, config):
        self._true_msg = config['true']
        self._false_msg = config['false']
        
    def toggle(self, state):
        msg = self._true_msg if state else self._false_msg
        if msg: print(msg, flush=True)
      
class PrintMsg(sink.RunnerSink):
    def __init__(self, config):
        super().__init__(config)
        self._msg = config.get('msg', 'message')
    def run(self):
        print(self._msg, flush=True)
        
