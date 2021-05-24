from actuator import source
import time

class TimeSource(source.Source):
    def __init__(self, config):
        super().__init__(config)
        self._format = config.get('format', '%H:%M:%S')
        
    @property
    def delay(self): 
        return self._delay or source.DELAY_SHORT
        

    #return a boolean
    @property
    def value(self):
        import datetime
        now = datetime.datetime.now().time()
        return now.strftime(self._format)


class EpochSource(source.Source):
    def __init__(self, config):
        super().__init__(config)

    @property
    def delay(self): 
        return self._delay or source.DELAY_SHORT

    @property
    def value(self):
        return time.time()
        

class DuringSource(source.Source):
    def __init__(self, config):
        super().__init__(config)
        self._start = DuringSource.parse(config['start'])
        self._end = DuringSource.parse(config['end'])
    
    @staticmethod
    def parse(s):
        from dateutil import parser
        return parser.parse(s).time()
    
    @property
    def delay(self): 
        return self._delay or source.DELAY_SHORT
    
    #return a boolean
    @property
    def value(self):
        import datetime
        now = datetime.datetime.now().time()
        
        if self._end < self._start:
            #end time is tomorrow
            return self._start <= now or now < self._end
        else:
            #end time is today
            return self._start <= now and now < self._end
        
            

