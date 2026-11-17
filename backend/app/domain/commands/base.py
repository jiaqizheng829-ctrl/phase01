from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Any, ClassVar
from uuid import UUID

from app.domain.actuators.ports import ActuatorPort


class Command(ABC):
    command_type: ClassVar[str]
    target_state: ClassVar[str]
    device_type: ClassVar[str]

    def __init__(
        self,
        device_id: UUID,
        payload: dict[str, Any] | None = None,
    ) -> None:
        self.device_id = device_id
        self.payload = deepcopy(payload if payload is not None else {})

    @abstractmethod
    def execute(self, port: ActuatorPort) -> None:
        """Execute through the supplied decorated port."""
        raise NotImplementedError