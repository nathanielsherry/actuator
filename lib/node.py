from actuator import util, component
import threading

class Node(component.Component):
    def __init__(self, source, sink, operator, monitor, name):
        super().__init__({})
        self._operator = operator
        self._source = source
        self._sink = sink
        self._monitor = monitor
        self._name = name
        
        #Threading is done w/ a callable back into this object
        self._thread = None

        self._operator.upstreams[0].set_upstream(self._source)

    def start(self):
        self._thread = threading.Thread(target=lambda: self.run())
        self._thread.start()
        
    def join(self):
        self._thread.join()
        
    def run(self):
        self._monitor.start(self._operator, self._sink)
    
    @property
    def name(self): 
        return "{}:{}".format(self._name, super().name)
    
    @property
    def description_data(self):
        data = {self.name: {
            'source': self._source.description_data,
            'operator': self._operator.description_data,
            'sink': self._sink.description_data,
            'monitor': self._monitor.description_data
        }}
        return data
    
        
class NodeManager(component.Component):
    def __init__(self, nodes):
        super().__init__({})
        self._nodes = nodes
        
    def start(self):
        for node in self._nodes:
            node.start()
        for node in self._nodes:
            node.join()
    
    @property
    def description_data(self):
        return {self.name: [n.description_data for n in self._nodes]}

