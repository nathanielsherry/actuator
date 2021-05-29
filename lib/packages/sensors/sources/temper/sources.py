from actuator.source import Source

class Temper(Source):
    def __init__(self, config):
        super().__init__(config)

    @property
    def value(self):
        from . import temper
        t = temper.Temper()
        return t.read

