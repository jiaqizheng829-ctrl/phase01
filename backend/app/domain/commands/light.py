from app.domain.actuators.ports import ActuatorPort
from app.domain.commands.base import Command


class SetLightLevelCommand(Command):
    command_type = "set_light_level"
    target_state = "running"
    device_type = "grow_light"

    def execute(self, port: ActuatorPort) -> None:
        port.apply(self.device_id, "set_light_level", self.payload)