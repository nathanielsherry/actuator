from actuator.components.source import Source
from actuator import log, util

from actuator.components.decorators import parameter, argument, input, output, allarguments, source

@parameter('lat', 'real', 0.0, 'Latitude for localisation', parser=float)
@parameter('lon', 'real', 0.0, 'Latitude for localisation', parser=float)
@output('dict', 'Localised weather information')
class Fetch(Source):
    def initialise(self, *args, **kwargs):
        self._id = self.lookup_coords(self.params.lat, self.params.lon)
    
    def lookup_coords(self, lat, lon):
        import json
        url = "https://www.metaweather.com/api/location/search/?lattlong={},{}".format(lat, lon)
        log.debug("{} looking up weather data from {}".format(self.kind, url))
        doc = util.get_url(url)
        data = json.loads(doc)
        log.debug("{} received weather data: {}".format(self.kind, data))
        return int(data[0]['woeid'])

    @property
    def value(self):
        import json
        document = util.get_url("https://www.metaweather.com/api/location/{id}/".format(id=self._id))
        data = json.loads(document)
        return data


@parameter('low', 'real', None, 'Threshold temperature for daily low', parser=float)
@parameter('high', 'real', None, 'Threshold temperature for daily high', parser=float)
@parameter('days', 'real', 3, 'Number of days of forecasts to look at', parser=int)
class Range(Fetch):
    @property
    def value(self):
        data = super().value
        forecast = data['consolidated_weather'][:self.params.days]
        high = max([day['max_temp'] for day in forecast])
        low = max([day['min_temp'] for day in forecast])
        log.debug("{kind} received weather data: high={high}, low={low}".format(kind=self.kind, low=low, high=high))
        
        return high, low




@output('bool', 'True if all given conditions are satisfied')
class Below(Range):
    @property
    def value(self):
        high, low = super().value
        
        if self.params.low == None and self.params.high == None:
            return False
        if self.params.low != None:
            if self.params.low <= low: return False
        if self.params.high != None:
            if self.params.high <= high: return False
        
        #No failure conditions encountered
        return True
        

@output('bool', 'True if all given conditions are satisfied')
class Above(Range):
    @property
    def value(self):
        high, low = super().value
        
        if self.params.low == None and self.params.high == None:
            return False
        if self.params.low != None:
            if self.params.low >= low: return False
        if self.params.high != None:
            if self.params.high >= high: return False
        
        #No failure conditions encountered
        return True
