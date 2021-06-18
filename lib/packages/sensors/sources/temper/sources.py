from actuator.components.source import Source

class Temper(Source):
    @property
    def value(self):
        from . import temper
        t = temper.Temper()
        return t.read

