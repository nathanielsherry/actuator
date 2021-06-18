from actuator.components import source
import time

class TimeSource(source.Source):
    def initialise(self, *args, **kwargs):
        super().initialise(*args, **kwargs)
        self._format = kwargs.get('format', '%H:%M:%S')
        
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
    @property
    def delay(self): 
        return self._delay or source.DELAY_SHORT

    @property
    def value(self):
        return time.time()
        

class DuringSource(source.Source):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._start = DuringSource.parse(kwargs['start'])
        self._end = DuringSource.parse(kwargs['end'])
    
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
        
            

