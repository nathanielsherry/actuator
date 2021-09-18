from actuator.components import source
import datetime, time

from actuator.components.decorators import parameter, argument, input, output, allarguments

@parameter('format', 'str', '%H:%M:%S', 'Time format string, in Python strftime style')
@output('str', 'String timestamp of the current time')
class TimestampSource(source.Source):   
    """
    Emits a string timestamp of the current time, formatted by the 
    format string as interpreted by Python's strftime function. 
    """
    @property
    def value(self):
        import datetime
        now = datetime.datetime.now()
        return now.strftime(self.params.format)


@output('datetime', 'Python datetime.datetime object')
class NowSource(source.Source):   
    @property
    def value(self):
        import datetime
        return datetime.datetime.now()

@parameter('floor', 'bool', True, 'Round this real-valued payload down to the int below it')
@output('real, int', 'Epoch time')
class EpochSource(source.Source):
    """
    Emits an epoch time, either as a real value (default) or an int.
    """
    @property
    def value(self):
        import math
        epoch = time.time()
        if self.params.floor: epoch = math.floor(epoch)
        return epoch
        

def parse_timestamp(s):
    from dateutil import parser
    return parser.parse(s).time()

@parameter('start', 'timestamp', None, 'Time (not date) stamp for lower range bound', parser=parse_timestamp)
@parameter('end', 'timestamp', None, 'Time (not date) stamp for upper range bound', parser=parse_timestamp)
class DuringSource(source.Source):
    """  
    Tests if the given datetime.datetime payload is between the start and 
    end parameters. These parameters should be given in a way that can be read
    by Python's dateutil.parser    
    """
    @property
    def value(self):
        import datetime
        now = datetime.datetime.now().time()
        
        if self.params.end < self.params.start:
            #end time is tomorrow
            return self.params.start <= now or now < self.params.end
        else:
            #end time is today
            return self.params.start <= now and now < self.params.end
        
            

