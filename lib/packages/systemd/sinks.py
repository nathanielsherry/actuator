from actuator.components.sink import ToggleSink

class Toggle(ToggleSink):
    def initialise(self, *args, **kwargs):
        super().initialise(*args, **kwargs)
        self._service = args[0]
        
    def toggle(self, payload):
        import subprocess
        subprocess.run(["systemctl", "start" if payload == True else "stop", self._service])
        
        

