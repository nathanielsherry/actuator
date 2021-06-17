from actuator.components.source import Source
from actuator import log, util

class Fetch(Source):
    def initialise(self, *args, **kwargs):
        super().initialise(*args, **kwargs)
        log.debug("{kind} received initial config {config}".format(kind=self.kind, config=(args, kwargs)))
        coords = kwargs['coords']
        lat, lon = coords.split(',')
        lat = float(lat)
        lon = float(lon)
        self._id = self.lookup_coords(lat, lon)
        
    
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


class Comparison(Fetch):
    def initialise(self, *args, **kwargs):
        super().initialise(*args, **kwargs)
        self._days = int(kwargs.get('days', '3'))
        self._low = kwargs.get('low', None)
        self._high = kwargs.get('high', None)
        if self._low: self._low = float(self._low)
        if self._high: self._high = float(self._high)

    @property
    def value(self):
        data = super().value
        forecast = data['consolidated_weather'][:self._days]
        high = max([day['max_temp'] for day in forecast])
        low = max([day['min_temp'] for day in forecast])
        log.debug("{kind} received weather data: high={high}, low={low}".format(kind=self.kind, low=low, high=high))
        
        return high, low

class Below(Comparison):
    @property
    def value(self):
        high, low = super().value
        if self._low == None and self._high == None:
            return False
        if self._low != None:
            if self._low <= low: return False
        if self._high != None:
            if self._high <= high: return False
        
        #No failure conditions encountered
        return True
        


class Above(Comparison):
    @property
    def value(self):
        high, low = super().value
        if self._low == None and self._high == None:
            return False
        if self._low != None:
            if self._low >= low: return False
        if self._high != None:
            if self._high >= high: return False

        #No failure conditions encountered
        return True