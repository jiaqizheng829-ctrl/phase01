from typing import Any
from uuid import UUID

from app.domain.actuators.ports import ActuatorPort
from app.domain.commands.base import Command
from app.domain.commands.light import SetLightLevelCommand
from app.domain.commands.pump import StartPumpCommand, StopPumpCommand


class UnknownCommandError(ValueError):
    pass


COMMAND_REGISTRY: dict[str, type[Command]] = {
    StartPumpCommand.command_type: StartPumpCommand,
    StopPumpCommand.command_type: StopPumpCommand,
    SetLightLevelCommand.command_type: SetLightLevelCommand,
}


class CommandInvoker:
    def create(
        self,
        command_type: str,
        device_id: UUID,
        payload: dict[str, Any] | None = None,
    ) -> Command:
        command_class = COMMAND_REGISTRY.get(command_type)

        if command_class is None:
            raise UnknownCommandError(
                f"Unknown command type: {command_type}"
            )

        return command_class(device_id, payload)

    def execute(self, command: Command, port: ActuatorPort) -> None:
        command.execute(port)