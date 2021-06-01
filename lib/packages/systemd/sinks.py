from actuator.components.sink import ToggleSink

class Toggle(ToggleSink):
    def __init__(self, config):
        self._service = config['args'][0]
        
    def toggle(self, payload):
        import subprocess
        subprocess.run(["systemctl", "start" if payload == True else "stop", self._service])
        
        

