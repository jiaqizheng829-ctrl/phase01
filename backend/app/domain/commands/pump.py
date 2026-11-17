from app.domain.actuators.ports import ActuatorPort
from app.domain.commands.base import Command


class StartPumpCommand(Command):
    command_type = "start_pump"
    target_state = "running"
    device_type = "water_pump"

    def execute(self, port: ActuatorPort) -> None:
        port.apply(self.device_id, "start", self.payload)


class StopPumpCommand(Command):
    command_type = "stop_pump"
    target_state = "idle"
    device_type = "water_pump"

    def execute(self, port: ActuatorPort) -> None:
        port.apply(self.device_id, "stop", self.payload)