from copy import deepcopy
from typing import Any
from uuid import UUID

from app.domain.actuators.ports import ActuatorPort


class SimulationActuatorAdapter(ActuatorPort):
    def __init__(self) -> None:
        self.commands: list[dict[str, Any]] = []

    def apply(
        self,
        device_id: UUID,
        command: str,
        payload: dict[str, Any],
    ) -> None:
        if not isinstance(device_id, UUID):
            raise ValueError("device_id must be a UUID.")

        if not isinstance(command, str) or not command.strip():
            raise ValueError("An actuator command is required.")

        if not isinstance(payload, dict):
            raise ValueError("Command payload must be an object.")

        self.commands.append(
            {
                "device_id": device_id,
                "command": command.strip(),
                "payload": deepcopy(payload),
            }
        )